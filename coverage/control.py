"""Core control stuff for coverage.py"""

import os, re, sys

from coverage.data import CoverageData
from coverage.misc import nice_pair, CoverageException
from coverage.codeunit import code_unit_factory
from coverage.files import FileLocator

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
    
        # Cache of results of calling the analysis2() method, so that you can
        # specify both -r and -a without doing double work.
        self.analysis_cache = {}
    
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
        self.analysis_cache = {}
        
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
        self.analysis_cache = {}
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

    # analyze_morf(morf).  Analyze the module or filename passed as
    # the argument.  If the source code can't be found, raise an error.
    # Otherwise, return a tuple of (1) the canonical filename of the
    # source code for the module, (2) a list of lines of statements
    # in the source code, (3) a list of lines of excluded statements,
    # and (4), a map of line numbers to multi-line line number ranges, for
    # statements that cross lines.

    # The word "morf" means a module object (from which the source file can
    # be deduced by suitable manipulation of the __file__ attribute) or a
    # filename.
    
    def analyze_morf(self, morf):
        from coverage.analyzer import CodeAnalyzer

        if self.analysis_cache.has_key(morf.filename):
            return self.analysis_cache[morf.filename]
        filename = morf.filename
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
                        "No source for code '%s'." % morf.filename
                        )

        analyzer = CodeAnalyzer()
        lines, excluded_lines, line_map = analyzer.analyze_source(
            text=source, filename=filename, exclude=self.exclude_re
            )

        result = filename, lines, excluded_lines, line_map
        self.analysis_cache[morf.filename] = result
        return result

    # format_lines(statements, lines).  Format a list of line numbers
    # for printing by coalescing groups of lines as long as the lines
    # represent consecutive statements.  This will coalesce even if
    # there are gaps between statements, so if statements =
    # [1,2,3,4,5,10,11,12,13,14] and lines = [1,2,5,10,11,13,14] then
    # format_lines will return "1-2, 5-11, 13-14".

    def format_lines(self, statements, lines):
        pairs = []
        i = 0
        j = 0
        start = None
        pairs = []
        while i < len(statements) and j < len(lines):
            if statements[i] == lines[j]:
                if start == None:
                    start = lines[j]
                end = lines[j]
                j = j + 1
            elif start:
                pairs.append((start, end))
                start = None
            i = i + 1
        if start:
            pairs.append((start, end))
        ret = ', '.join(map(nice_pair, pairs))
        return ret

    # Backward compatibility with version 1.
    def analysis(self, morf):
        f, s, _, m, mf = self.analysis2(morf)
        return f, s, m, mf

    def analysis2(self, morf):
        code_units = code_unit_factory(morf, self.file_locator)
        return self.analysis_engine(code_units[0])

    def analysis_engine(self, morf):
        filename, statements, excluded, line_map = self.analyze_morf(morf)
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
                self.format_lines(statements, missing))

    # Programmatic entry point
    def report(self, morfs, show_missing=True, ignore_errors=False, file=None):
        self.report_engine(morfs, show_missing=show_missing, ignore_errors=ignore_errors, file=file)

    def report_engine(self, morfs, show_missing=True, ignore_errors=False, file=None, omit_prefixes=None):
        morfs = morfs or self.data.executed_files()
        code_units = code_unit_factory(morfs, self.file_locator, omit_prefixes)
        code_units.sort()

        max_name = max(5, max(map(lambda cu: len(cu.name), code_units)))
        fmt_name = "%%- %ds  " % max_name
        fmt_err = fmt_name + "%s: %s"
        header = fmt_name % "Name" + " Stmts   Exec  Cover"
        fmt_coverage = fmt_name + "% 6d % 6d % 5d%%"
        if show_missing:
            header = header + "   Missing"
            fmt_coverage = fmt_coverage + "   %s"
        if not file:
            file = sys.stdout
        print >>file, header
        print >>file, "-" * len(header)
        total_statements = 0
        total_executed = 0
        for cu in code_units:
            try:
                _, statements, _, missing, readable = self.analysis_engine(cu)
                n = len(statements)
                m = n - len(missing)
                if n > 0:
                    pc = 100.0 * m / n
                else:
                    pc = 100.0
                args = (cu.name, n, m, pc)
                if show_missing:
                    args = args + (readable,)
                print >>file, fmt_coverage % args
                total_statements = total_statements + n
                total_executed = total_executed + m
            except KeyboardInterrupt:                       #pragma: no cover
                raise
            except:
                if not ignore_errors:
                    typ, msg = sys.exc_info()[:2]
                    print >>file, fmt_err % (cu.name, typ, msg)
        if len(code_units) > 1:
            print >>file, "-" * len(header)
            if total_statements > 0:
                pc = 100.0 * total_executed / total_statements
            else:
                pc = 100.0
            args = ("TOTAL", total_statements, total_executed, pc)
            if show_missing:
                args = args + ("",)
            print >>file, fmt_coverage % args

    # annotate(morfs, ignore_errors).

    blank_re = re.compile(r"\s*(#|$)")
    else_re = re.compile(r"\s*else\s*:\s*(#|$)")

    def annotate(self, morfs, directory=None, ignore_errors=False, omit_prefixes=None):
        morfs = morfs or self.data.executed_files()
        code_units = code_unit_factory(morfs, self.file_locator, omit_prefixes)
        for cu in code_units:
            try:
                filename, statements, excluded, missing, _ = self.analysis_engine(cu)
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
