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

        for fr, analysis in get_analysis_to_report(self.coverage, morfs):
            self.total += analysis.numbers
            self.lcov_file(fr, analysis, outfile)

        return self.total.n_statements and self.total.pc_covered

    def lcov_file(self, fr: FileReporter, analysis: Analysis, outfile: IO[str]) -> None:
        """Produces the lcov data for a single file.

        This currently supports both line and branch coverage,
        however function coverage is not supported.
        """
        if analysis.numbers.n_statements == 0:
            if self.config.skip_empty:
                return

        outfile.write(f"SF:{fr.relative_filename()}\n")
        if self.checksum_mode == "file":
            outfile.write(f"VER:{file_hash(fr.source())}\n")

        source_lines = fr.source().splitlines()
        for covered in sorted(analysis.executed):
            if covered in analysis.excluded:
                # Do not report excluded as executed
                continue

            if source_lines:
                if covered-1 >= len(source_lines):
                    break
                line = source_lines[covered-1]
            else:
                line = ""
            if self.checksum_mode == "line":
                hash_suffix = "," + line_hash(line)
            else:
                hash_suffix = ""

            # Note: Coverage.py currently only supports checking *if* a line
            # has been executed, not how many times, so we set this to 1 for
            # nice output even if it's technically incorrect.
            outfile.write(f"DA:{covered},1{hash_suffix}\n")

        for missed in sorted(analysis.missing):
            # We don't have to skip excluded lines here, because `missing`
            # already doesn't have them.
            assert source_lines
            line = source_lines[missed-1]
            if self.checksum_mode == "line":
                hash_suffix = "," + line_hash(line)
            else:
                hash_suffix = ""
            outfile.write(f"DA:{missed},0{hash_suffix}\n")

        if analysis.numbers.n_statements > 0:
            outfile.write(f"LF:{analysis.numbers.n_statements}\n")
            outfile.write(f"LH:{analysis.numbers.n_executed}\n")

        # More information dense branch coverage data.
        missing_arcs = analysis.missing_branch_arcs()
        executed_arcs = analysis.executed_branch_arcs()
        for block_number, block_line_number in enumerate(
            sorted(analysis.branch_stats().keys()),
        ):
            for branch_number, line_number in enumerate(
                sorted(missing_arcs[block_line_number]),
            ):
                # The exit branches have a negative line number,
                # this will not produce valid lcov. Setting
                # the line number of the exit branch to 0 will allow
                # for valid lcov, while preserving the data.
                line_number = max(line_number, 0)
                outfile.write(f"BRDA:{line_number},{block_number},{branch_number},-\n")

            # The start value below allows for the block number to be
            # preserved between these two for loops (stopping the loop from
            # resetting the value of the block number to 0).
            for branch_number, line_number in enumerate(
                sorted(executed_arcs[block_line_number]),
                start=len(missing_arcs[block_line_number]),
            ):
                line_number = max(line_number, 0)
                outfile.write(f"BRDA:{line_number},{block_number},{branch_number},1\n")

        # Summary of the branch coverage.
        if analysis.has_arcs:
            branch_stats = analysis.branch_stats()
            brf = sum(t for t, k in branch_stats.values())
            brh = brf - sum(t - k for t, k in branch_stats.values())
            if brf > 0:
                outfile.write(f"BRF:{brf}\n")
                outfile.write(f"BRH:{brh}\n")

        outfile.write("end_of_record\n")
