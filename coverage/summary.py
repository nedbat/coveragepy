"""Summary reporting"""

import sys

from coverage.report import Reporter


class SummaryReporter(Reporter):
    """A reporter for writing the summary report."""
    
    def __init__(self, coverage, show_missing=True, ignore_errors=False):
        super(SummaryReporter, self).__init__(coverage, ignore_errors)
        self.show_missing = show_missing

    def report(self, morfs, omit_prefixes=None, outfile=None):
        """Writes a report summarizing coverage statistics per module."""
        
        from coverage.control import Numbers
        self.find_code_units(morfs, omit_prefixes)

        # Prepare the formatting strings
        max_name = max([len(cu.name) for cu in self.code_units] + [5])
        fmt_name = "%%- %ds  " % max_name
        fmt_err = "%s   %s: %s\n"
        header = fmt_name % "Name" + " Stmts   Exec  Cover\n"
        fmt_coverage = fmt_name + "% 6d % 6d % 5d%%\n"
        if self.show_missing:
            header = header.replace("\n", "   Missing\n")
            fmt_coverage = fmt_coverage.replace("\n", "   %s\n")
        rule = "-" * (len(header)-1) + "\n"

        if not outfile:
            outfile = sys.stdout

        # Write the header
        outfile.write(header)
        outfile.write(rule)

        total = Numbers()
        
        for cu in self.code_units:
            try:
                analysis = self.coverage._analyze(cu)
                nums = analysis.numbers
                args = (cu.name, nums.n_statements, nums.n_run, nums.percent_covered)
                if self.show_missing:
                    args = args + (analysis.missing_formatted(),)
                outfile.write(fmt_coverage % args)
                total += nums
            except KeyboardInterrupt:                       #pragma: no cover
                raise
            except:
                if not self.ignore_errors:
                    typ, msg = sys.exc_info()[:2]
                    outfile.write(fmt_err % (cu.name, typ.__name__, msg))

        if total.n_files > 1:
            outfile.write(rule)
            args = ("TOTAL", total.n_statements, total.n_run, total.percent_covered)
            if self.show_missing:
                args = args + ("",)
            outfile.write(fmt_coverage % args)
