"""Core control stuff for Coverage."""

import os, socket, sys

from coverage.annotate import AnnotateReporter
from coverage.codeunit import code_unit_factory
from coverage.data import CoverageData
from coverage.files import FileLocator
from coverage.html import HtmlReporter
from coverage.misc import format_lines, CoverageException
from coverage.summary import SummaryReporter

class coverage:
    def __init__(self):
        from coverage.collector import Collector
        from coverage import __version__
        
        self.parallel_mode = False
        self.exclude_re = ''
        self.cover_stdlib = False
        self.nesting = 0
        
        self.file_locator = FileLocator()
        self.sysprefix = self.file_locator.abs_file(sys.prefix)
        
        self.collector = Collector(self.should_trace)
        self.data = CoverageData(collector="coverage v%s" % __version__)
    
        # The default exclude pattern.
        self.exclude('# *pragma[: ]*[nN][oO] *[cC][oO][vV][eE][rR]')

        # Save coverage data when Python exits.
        import atexit
        atexit.register(self.save)

    def should_trace(self, filename):
        """Decide whether to trace execution in `filename`
        
        Returns a canonicalized filename if it should be traced, False if it
        should not.
        
        """
        if filename == '<string>':
            # There's no point in ever tracing string executions, we can't do
            # anything with the data later anyway.
            return False
        
        canonical = self.file_locator.canonical_filename(filename)
        if not self.cover_stdlib:
            if canonical.startswith(self.sysprefix):
                return False
        
        # TODO: ignore by module as well as file?
        return canonical

    def use_cache(self, usecache):
        """Control the use of a data file (incorrectly called a cache).
        
        `usecache` is true or false, whether to read and write data on disk.
        
        """
        self.data.usefile(usecache)

    def get_ready(self):
        self.collector.reset()
        if self.parallel_mode:
            self.data.set_suffix("%s.%s" % (socket.gethostname(), os.getpid()))
        self.data.read()
        
    def start(self):
        self.get_ready()
        if self.nesting == 0:                               #pragma: no cover
            self.collector.start()
        self.nesting += 1
        
    def stop(self):
        self.nesting -= 1
        if self.nesting == 0:                               #pragma: no cover
            self.collector.stop()

    def erase(self):
        self.get_ready()
        self.collector.reset()
        self.data.erase()

    def exclude(self, regex):
        """Exclude source lines from execution consideration.
        
        `regex` is a regular expression.  Lines matching this expression are
        not considered executable when reporting code coverage.  A list of
        regexes is maintained; this function adds a new regex to the list.
        Matching any of the regexes excludes a source line.
        
        """
        if self.exclude_re:
            self.exclude_re += "|"
        self.exclude_re += "(" + regex + ")"

    def save(self):
        self.group_collected_data()
        self.data.write()

    def combine(self):
        """Entry point for combining together parallel-mode coverage data."""
        self.data.combine_parallel_data()

    def group_collected_data(self):
        """Group the collected data by filename and reset the collector."""
        self.data.add_line_data(self.collector.data_points())
        self.collector.reset()

    # Backward compatibility with version 1.
    def analysis(self, morf):
        f, s, _, m, mf = self.analysis2(morf)
        return f, s, m, mf

    def analysis2(self, morf):
        code_unit = code_unit_factory(morf, self.file_locator)[0]
        st, ex, m, mf = self.analyze(code_unit)
        return code_unit.filename, st, ex, m, mf

    def analyze(self, code_unit):
        """Analyze a single code unit.
        
        Returns a tuple of:
        - a list of lines of statements in the source code,
        - a list of lines of excluded statements,
        - a list of lines missing from execution, and
        - a readable string of missing lines.

        """
        from coverage.parser import CodeParser

        filename = code_unit.filename
        ext = os.path.splitext(filename)[1]
        source = None
        if ext == '.py':
            if not os.path.exists(filename):
                source = self.file_locator.get_zip_data(filename)
                if not source:
                    raise CoverageException(
                        "No source for code '%s'." % code_unit.filename
                        )

        parser = CodeParser()
        statements, excluded, line_map = parser.parse_source(
            text=source, filename=filename, exclude=self.exclude_re
            )

        self.group_collected_data()
        
        # Identify missing statements.
        missing = []
        execed = self.data.executed_lines(filename)
        for line in statements:
            lines = line_map.get(line)
            if lines:
                for l in range(lines[0], lines[1]+1):
                    if l in execed:
                        break
                else:
                    missing.append(line)
            else:
                if line not in execed:
                    missing.append(line)

        return (
            statements, excluded, missing, format_lines(statements, missing)
            )

    def report(self, morfs, show_missing=True, ignore_errors=False, file=None,
                omit_prefixes=None
                ):
        """Write a summary report to `file`.
        
        Each module in `morfs` is listed, with counts of statements, executed
        statements, missing statements, and a list of lines missed.
        
        """
        reporter = SummaryReporter(self, show_missing, ignore_errors)
        reporter.report(morfs, outfile=file, omit_prefixes=omit_prefixes)

    def annotate(self, morfs, directory=None, ignore_errors=False,
                omit_prefixes=None
                ):
        """Annotate a list of modules.
        
        Each module in `morfs` is annotated.  The source is written to a new
        file, named with a ",cover" suffix, with each line prefixed with a
        marker to indicate the coverage of the line.  Covered lines have ">",
        excluded lines have "-", and missing lines have "!".
        
        """
        reporter = AnnotateReporter(self, ignore_errors)
        reporter.report(morfs, directory=directory, omit_prefixes=omit_prefixes)

    def html_report(self, morfs, directory=None, ignore_errors=False,
                omit_prefixes=None
                ):
        """Generate an HTML report.
        
        """
        reporter = HtmlReporter(self, ignore_errors)
        reporter.report(morfs, directory=directory, omit_prefixes=omit_prefixes)
