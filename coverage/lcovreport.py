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


class LcovReporter:
    """A reporter for writing LCOV coverage reports."""

    report_type = "LCOV report"

    def __init__(self, coverage: Coverage) -> None:
        self.coverage = coverage
        self.config = coverage.config
        self.total = Numbers(self.coverage.config.precision)

    def report(self, morfs: Iterable[TMorf] | None, outfile: IO[str]) -> float:
        """Renders the full lcov report.

        `morfs` is a list of modules or filenames

        outfile is the file object to write the file into.
        """

        self.coverage.get_data()
        outfile = outfile or sys.stdout

        # ensure file records are sorted by the _relative_ filename, not the full path
        to_report = [
            (fr.relative_filename(), fr, analysis)
            for fr, analysis in get_analysis_to_report(self.coverage, morfs)
        ]
        to_report.sort()

        for fname, fr, analysis in to_report:
            self.total += analysis.numbers
            self.lcov_file(fname, fr, analysis, outfile)

        return self.total.n_statements and self.total.pc_covered

    def lcov_file(
        self,
        rel_fname: str,
        fr: FileReporter,
        analysis: Analysis,
        outfile: IO[str],
    ) -> None:
        """Produces the lcov data for a single file.

        This currently supports both line and branch coverage,
        however function coverage is not supported.
        """

        if analysis.numbers.n_statements == 0:
            if self.config.skip_empty:
                return

        outfile.write(f"SF:{rel_fname}\n")

        if self.config.lcov_line_checksums:
            source_lines = fr.source().splitlines()

        # Emit a DA: record for each line of the file.
        lines = sorted(analysis.statements)
        hash_suffix = ""
        for line in lines:
            if self.config.lcov_line_checksums:
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
                    # The meaning of a BRDA: line is not well explained in the lcov
                    # documentation.  Based on what genhtml does with them, however,
                    # the interpretation is supposed to be something like this:
                    # BRDA: <line>, <block>, <branch>, <hit>
                    # where <line> is the source line number of the *origin* of the
                    # branch; <block> is an arbitrary number which distinguishes multiple
                    # control flow operations on a single line; <branch> is an arbitrary
                    # number which distinguishes the possible destinations of the specific
                    # control flow operation identified by <line> + <block>; and <hit> is
                    # either the hit count for <line> + <block> + <branch> or "-" meaning
                    # that <line> + <block> was never *reached*.  <line> must be >= 1,
                    # and <block>, <branch>, <hit> must be >= 0.

                    # This is only one possible way to map our sets of executed and
                    # not-executed arcs to BRDA codes. It seems to produce reasonable
                    # results when fed through genhtml.

                    # Q: can we get counts of the number of times each arc was executed?
                    # branch_stats has "total" and "taken" counts for each branch, but it
                    # doesn't have "taken" broken down by destination.
                    destinations = {}
                    for dst in executed_arcs[line]:
                        destinations[(int(dst < 0), abs(dst))] = 1
                    for dst in missing_arcs[line]:
                        destinations[(int(dst < 0), abs(dst))] = 0

                    if all(v == 0 for v in destinations.values()):
                        # When _none_ of the out arcs from 'line' were executed, presume
                        # 'line' was never reached.
                        for branch, _ in enumerate(sorted(destinations.keys())):
                            outfile.write(f"BRDA:{line},0,{branch},-\n")
                    else:
                        for branch, (_, hit) in enumerate(sorted(destinations.items())):
                            outfile.write(f"BRDA:{line},0,{branch},{hit}\n")

            # Summary of the branch coverage.
            brf = sum(t for t, k in branch_stats.values())
            brh = brf - sum(t - k for t, k in branch_stats.values())
            if brf > 0:
                outfile.write(f"BRF:{brf}\n")
                outfile.write(f"BRH:{brh}\n")

        outfile.write("end_of_record\n")
