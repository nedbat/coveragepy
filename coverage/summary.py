"""Summary reporting"""

import sys

from coverage.codeunit import code_unit_factory

class SummaryReporter:
    """A reporter for writing the summary report."""
    
    def __init__(self, coverage, show_missing=True, ignore_errors=False):
        self.coverage = coverage
        self.show_missing = show_missing
        self.ignore_errors = ignore_errors

    def report(self, morfs, omit_prefixes=None, outfile=None):
        """Writes a report summarizing coverage statistics per module."""
        
        morfs = morfs or self.coverage.data.executed_files()
        code_units = code_unit_factory(morfs, self.coverage.file_locator, omit_prefixes)
        code_units.sort()

        max_name = max(5, max(map(lambda cu: len(cu.name), code_units)))
        fmt_name = "%%- %ds  " % max_name
        fmt_err = fmt_name + "%s: %s"
        header = fmt_name % "Name" + " Stmts   Exec  Cover"
        fmt_coverage = fmt_name + "% 6d % 6d % 5d%%"
        if self.show_missing:
            header = header + "   Missing"
            fmt_coverage = fmt_coverage + "   %s"
        if not outfile:
            outfile = sys.stdout
        print >>outfile, header
        print >>outfile, "-" * len(header)
        total_statements = 0
        total_executed = 0
        for cu in code_units:
            try:
                _, statements, _, missing, readable = self.coverage.analyze(cu)
                n = len(statements)
                m = n - len(missing)
                if n > 0:
                    pc = 100.0 * m / n
                else:
                    pc = 100.0
                args = (cu.name, n, m, pc)
                if self.show_missing:
                    args = args + (readable,)
                print >>outfile, fmt_coverage % args
                total_statements = total_statements + n
                total_executed = total_executed + m
            except KeyboardInterrupt:                       #pragma: no cover
                raise
            except:
                if not self.ignore_errors:
                    typ, msg = sys.exc_info()[:2]
                    print >>outfile, fmt_err % (cu.name, typ, msg)
        if len(code_units) > 1:
            print >>outfile, "-" * len(header)
            if total_statements > 0:
                pc = 100.0 * total_executed / total_statements
            else:
                pc = 100.0
            args = ("TOTAL", total_statements, total_executed, pc)
            if self.show_missing:
                args = args + ("",)
            print >>outfile, fmt_coverage % args
