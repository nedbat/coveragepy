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
        
        self.find_code_units(morfs, omit_prefixes)

        # Prepare the formatting strings
        max_name = max(5, max(map(lambda cu: len(cu.name), self.code_units)))
        fmt_name = "%%- %ds  " % max_name
        fmt_err = fmt_name + "%s: %s\n"
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

        total_statements = 0
        total_executed = 0
        total_units = 0
        
        for cu in self.code_units:
            try:
                statements, _, missing, readable = self.coverage.analyze(cu)
                n = len(statements)
                m = n - len(missing)
                if n > 0:
                    pc = 100.0 * m / n
                else:
                    pc = 100.0
                args = (cu.name, n, m, pc)
                if self.show_missing:
                    args = args + (readable,)
                outfile.write(fmt_coverage % args)
                total_units += 1
                total_statements = total_statements + n
                total_executed = total_executed + m
            except KeyboardInterrupt:                       #pragma: no cover
                raise
            except:
                if not self.ignore_errors:
                    typ, msg = sys.exc_info()[:2]
                    outfile.write(fmt_err % (cu.name, typ, msg))

        if total_units > 1:
            outfile.write(rule)
            if total_statements > 0:
                pc = 100.0 * total_executed / total_statements
            else:
                pc = 100.0
            args = ("TOTAL", total_statements, total_executed, pc)
            if self.show_missing:
                args = args + ("",)
            outfile.write(fmt_coverage % args)
