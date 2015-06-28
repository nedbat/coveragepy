"""Summary reporting"""

import sys

from coverage.report import Reporter
from coverage.results import Numbers
from coverage.misc import NotPython


class SummaryReporter(Reporter):
    """A reporter for writing the summary report."""

    def __init__(self, coverage, config):
        super(SummaryReporter, self).__init__(coverage, config)
        self.branches = coverage.data.has_arcs()

    def report(self, morfs, outfile=None):
        """Writes a report summarizing coverage statistics per module.

        `outfile` is a file object to write the summary to.

        """
        self.find_file_reporters(morfs)

        # Prepare the formatting strings
        max_name = max([len(fr.name) for fr in self.file_reporters] + [5])
        fmt_name = "%%- %ds  " % max_name
        fmt_err = "%s   %s: %s\n"
        header = (fmt_name % "Name") + " Stmts   Miss"
        fmt_coverage = fmt_name + "%6d %6d"
        if self.branches:
            header += " Branch BrPart"
            fmt_coverage += " %6d %6d"
        width100 = Numbers.pc_str_width()
        header += "%*s" % (width100+4, "Cover")
        fmt_coverage += "%%%ds%%%%" % (width100+3,)
        if self.config.show_missing:
            header += "   Missing"
            fmt_coverage += "   %s"
        rule = "-" * len(header) + "\n"
        header += "\n"
        fmt_coverage += "\n"

        if not outfile:
            outfile = sys.stdout

        # Write the header
        outfile.write(header)
        outfile.write(rule)

        total = Numbers()

        for fr in self.file_reporters:
            try:
                analysis = self.coverage._analyze(fr)
                nums = analysis.numbers

                if self.config.skip_covered:
                    # Don't report on 100% files.
                    no_missing_lines = (nums.n_missing == 0)
                    if self.branches:
                        no_missing_branches = (nums.n_partial_branches == 0)
                    else:
                        no_missing_branches = True
                    if no_missing_lines and no_missing_branches:
                        continue

                args = (fr.name, nums.n_statements, nums.n_missing)
                if self.branches:
                    args += (nums.n_branches, nums.n_partial_branches)
                args += (nums.pc_covered_str,)
                if self.config.show_missing:
                    missing_fmtd = analysis.missing_formatted()
                    if self.branches:
                        branches_fmtd = analysis.arcs_missing_formatted()
                        if branches_fmtd:
                            if missing_fmtd:
                                missing_fmtd += ", "
                            missing_fmtd += branches_fmtd
                    args += (missing_fmtd,)
                outfile.write(fmt_coverage % args)
                total += nums
            except Exception:
                report_it = not self.config.ignore_errors
                if report_it:
                    typ, msg = sys.exc_info()[:2]
                    if typ is NotPython and not fr.should_be_python():
                        report_it = False
                if report_it:
                    outfile.write(fmt_err % (fr.name, typ.__name__, msg))

        if total.n_files > 1:
            outfile.write(rule)
            args = ("TOTAL", total.n_statements, total.n_missing)
            if self.branches:
                args += (total.n_branches, total.n_partial_branches)
            args += (total.pc_covered_str,)
            if self.config.show_missing:
                args += ("",)
            outfile.write(fmt_coverage % args)

        return total.n_statements and total.pc_covered
