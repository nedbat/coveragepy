"""Core control stuff for coverage.py"""

import os, re, sys

from coverage.codeunit import code_unit_factory
from coverage.data import CoverageData
from coverage.files import FileLocator
from coverage.misc import format_lines, CoverageException
from coverage.summary import SummaryReporter

class coverage:
    def __init__(self):
        from coverage.collector import Collector
        
        self.parallel_mode = False
        self.exclude_re = ''
        self.nesting = 0
        self.cstack = []
        self.xstack = []
        self.file_locator = FileLocator()
        
        self.collector = Collector(self.should_trace)
        
        self.data = CoverageData()
    
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
        # TODO: flag: ignore std lib?
        # TODO: ignore by module as well as file?
        return self.file_locator.canonical_filename(filename)

    def use_cache(self, usecache, cache_file=None):
        self.data.usefile(usecache, cache_file)
        
    def get_ready(self):
        self.collector.reset()
        self.data.read(parallel=self.parallel_mode)
        
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
        if self.exclude_re:
            self.exclude_re += "|"
        self.exclude_re += "(" + regex + ")"

    def begin_recursive(self):
        #self.cstack.append(self.c)
        self.xstack.append(self.exclude_re)
        
    def end_recursive(self):
        #self.c = self.cstack.pop()
        self.exclude_re = self.xstack.pop()

    def save(self):
        self.group_collected_data()
        self.data.write()

    def combine(self):
        """Entry point for combining together parallel-mode coverage data."""
        self.data.combine_parallel_data()

    def group_collected_data(self):
        """Group the collected data by filename and reset the collector."""
        self.data.add_raw_data(self.collector.data_points())
        self.collector.reset()

    # Backward compatibility with version 1.
    def analysis(self, morf):
        f, s, _, m, mf = self.analysis2(morf)
        return f, s, m, mf

    def analysis2(self, morf):
        code_units = code_unit_factory(morf, self.file_locator)
        return self.analyze(code_units[0])

    def analyze(self, code_unit):
        """Analyze a single code unit.
        
        Otherwise, return a tuple of (1) the canonical filename of the source
        code for the module, (2) a list of lines of statements in the source
        code, (3) a list of lines of excluded statements, (4) a list of lines
        missing from execution, and (5), a readable string of missing lines.

        """
        from coverage.analyzer import CodeAnalyzer

        filename = code_unit.filename
        ext = os.path.splitext(filename)[1]
        source = None
        if ext == '.pyc':
            filename = filename[:-1]
            ext = '.py'
        if ext == '.py':
            if not os.path.exists(filename):
                source = self.file_locator.get_zip_data(filename)
                if not source:
                    raise CoverageException(
                        "No source for code '%s'." % code_unit.filename
                        )

        analyzer = CodeAnalyzer()
        statements, excluded, line_map = analyzer.analyze_source(
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
                    
        return (filename, statements, excluded, missing,
                    format_lines(statements, missing))

    def report(self, morfs, show_missing=True, ignore_errors=False, file=None):
        """Write a summary report to `file`.
        
        Each module in `morfs` is listed, with counts of statements, executed
        statements, missing statements, and a list of lines missed.
        
        """
        reporter = SummaryReporter(self, show_missing, ignore_errors)
        reporter.report(morfs, outfile=file)

    # annotate(morfs, ignore_errors).

    blank_re = re.compile(r"\s*(#|$)")
    else_re = re.compile(r"\s*else\s*:\s*(#|$)")

    def annotate(self, morfs, directory=None, ignore_errors=False, omit_prefixes=None):
        morfs = morfs or self.data.executed_files()
        code_units = code_unit_factory(morfs, self.file_locator, omit_prefixes)
        for cu in code_units:
            try:
                filename, statements, excluded, missing, _ = self.analyze(cu)
                self.annotate_file(filename, statements, excluded, missing, directory)
            except KeyboardInterrupt:
                raise
            except:
                if not ignore_errors:
                    raise
                
    def annotate_file(self, filename, statements, excluded, missing, directory=None):
        source = open(filename, 'r')
        if directory:
            dest_file = os.path.join(directory,
                                     os.path.basename(filename)
                                     + ',cover')
        else:
            dest_file = filename + ',cover'
        dest = open(dest_file, 'w')
        lineno = 0
        i = 0
        j = 0
        covered = True
        while True:
            line = source.readline()
            if line == '':
                break
            lineno = lineno + 1
            while i < len(statements) and statements[i] < lineno:
                i = i + 1
            while j < len(missing) and missing[j] < lineno:
                j = j + 1
            if i < len(statements) and statements[i] == lineno:
                covered = j >= len(missing) or missing[j] > lineno
            if self.blank_re.match(line):
                dest.write('  ')
            elif self.else_re.match(line):
                # Special logic for lines containing only 'else:'.  
                if i >= len(statements) and j >= len(missing):
                    dest.write('! ')
                elif i >= len(statements) or j >= len(missing):
                    dest.write('> ')
                elif statements[i] == missing[j]:
                    dest.write('! ')
                else:
                    dest.write('> ')
            elif lineno in excluded:
                dest.write('- ')
            elif covered:
                dest.write('> ')
            else:
                dest.write('! ')
            dest.write(line)
        source.close()
        dest.close()
