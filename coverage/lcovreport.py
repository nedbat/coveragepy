# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""LCOV reporting for coverage.py."""

from __future__ import annotations

import base64
import hashlib
import sys

from typing import IO, Iterable, TYPE_CHECKING

from coverage.plugin import FileReporter
from coverage.report_core import get_analysis_to_report
from coverage.results import Analysis, Numbers
from coverage.types import TMorf

if TYPE_CHECKING:
    from coverage import Coverage


def line_hash(line: str) -> str:
    """Produce a hash of a source line for use in the LCOV file."""
    # The LCOV file format optionally allows each line to be MD5ed as a
    # fingerprint of the file.  This is not a security use.  Some security
    # scanners raise alarms about the use of MD5 here, but it is a false
    # positive.  This is not a security concern.
    # The unusual encoding of the MD5 hash, as a base64 sequence with the
    # trailing = signs stripped, is specified by the LCOV file format.
    hashed = hashlib.md5(line.encode("utf-8")).digest()
    return base64.b64encode(hashed).decode("ascii").rstrip("=")


def file_hash(file: str) -> str:
    """Produce a hash of an entire source file for use in the LCOV file."""
    # The LCOV file format optionally allows each entire file to be
    # fingerprinted, using a hash algorithm and format of the generator's
    # choice.  We use sha256 (unlike line hashes), with the result written out
    # in base64 with trailing = signs stripped (like line hashes).  See the
    # documentation of the 'checksums' option for how to tell the LCOV tools
    # to check these hashes.
    hashed = hashlib.sha256(file.encode("utf-8")).digest()
    return base64.b64encode(hashed).decode("ascii").rstrip("=")


class LcovReporter:
    """A reporter for writing LCOV coverage reports."""

    report_type = "LCOV report"

    def __init__(self, coverage: Coverage) -> None:
        self.coverage = coverage
        self.config = coverage.config
        self.checksum_mode = self.config.lcov_checksums.lower().strip()
        self.total = Numbers(self.coverage.config.precision)

        if self.checksum_mode not in ("file", "line", "off"):
            raise ValueError(f"invalid configuration, checksums = {self.checksum_mode!r}"
                             " not understood")

    def report(self, morfs: Iterable[TMorf] | None, outfile: IO[str]) -> float:
        """Renders the full lcov report.

        `morfs` is a list of modules or filenames

        outfile is the file object to write the file into.
        """

        self.coverage.get_data()
        outfile = outfile or sys.stdout

        # ensure file records are sorted by the _relative_ filename, not the full path
        to_report = [(fr.relative_filename(), fr, analysis)
                     for fr, analysis in get_analysis_to_report(self.coverage, morfs)]
        to_report.sort()

        for fname, fr, analysis in to_report:
            self.total += analysis.numbers
            self.lcov_file(fname, fr, analysis, outfile)

        return self.total.n_statements and self.total.pc_covered

    def lcov_file(self, rel_fname: str,
                  fr: FileReporter, analysis: Analysis,
                  outfile: IO[str]) -> None:
        """Produces the lcov data for a single file.

        This currently supports both line and branch coverage,
        however function coverage is not supported.
        """
        if analysis.numbers.n_statements == 0:
            if self.config.skip_empty:
                return

        outfile.write(f"SF:{rel_fname}\n")

        source_lines = None
        if self.checksum_mode == "line":
            source_lines = fr.source().splitlines()
        elif self.checksum_mode == "file":
            outfile.write(f"VER:{file_hash(fr.source())}\n")

        # Emit a DA: record for each line of the file.
        lines = sorted(analysis.statements)
        hash_suffix = ""
        for line in lines:
            if self.checksum_mode == "line":
                hash_suffix = "," + line_hash(source_lines[line-1])
            # Q: can we get info about the number of times a statement is
            # executed?  If so, that should be recorded here.
            hit = int(line not in analysis.missing)
            outfile.write(f"DA:{line},{hit}{hash_suffix}\n")

        if analysis.numbers.n_statements > 0:
            outfile.write(f"LF:{analysis.numbers.n_statements}\n")
            outfile.write(f"LH:{analysis.numbers.n_executed}\n")

        # More information dense branch coverage data, if available.
        if analysis.has_arcs:
            branch_stats = analysis.branch_stats()
            executed_arcs = analysis.executed_branch_arcs()
            missing_arcs = analysis.missing_branch_arcs()

            for line in lines:
                if line in branch_stats:
                    # In our data, exit branches have negative destination line numbers.
                    # The lcov tools will reject these - but the lcov tools consider the
                    # destinations of branches to be opaque tokens.  Use the absolute
                    # value of the destination line number as the destination block
                    # number, and its sign as the destination branch number.  This will
                    # ensure destinations are unique and stable, source line numbers are
                    # always positive, and destination block and branch numbers are always
                    # nonnegative, which are the properties we need.

                    # The data we have does not permit us to identify branches that were
                    # never *reached*, which is what "-" in the hit column means.  Such
                    # branches aren't in either executed_arcs or missing_arcs - we don't
                    # even know they exist.

                    # Q: can we get counts of the number of times each arc was executed?
                    # branch_stats has "total" and "taken" counts but it doesn't have
                    # "taken" broken down by destination.
                    arcs = []
                    arcs.extend((abs(l), int(l <= 0), 1) for l in executed_arcs[line])
                    arcs.extend((abs(l), int(l <= 0), 0) for l in missing_arcs[line])
                    arcs.sort()

                    for block, branch, hit in arcs:
                        outfile.write(f"BRDA:{line},{block},{branch},{hit}\n")

            # Summary of the branch coverage.
            brf = sum(t for t, k in branch_stats.values())
            brh = brf - sum(t - k for t, k in branch_stats.values())
            if brf > 0:
                outfile.write(f"BRF:{brf}\n")
                outfile.write(f"BRH:{brh}\n")

        outfile.write("end_of_record\n")
