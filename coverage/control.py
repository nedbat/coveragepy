"""Core control stuff for Coverage."""

import os, socket

from coverage.annotate import AnnotateReporter
from coverage.codeunit import code_unit_factory
from coverage.collector import Collector
from coverage.data import CoverageData
from coverage.files import FileLocator
from coverage.html import HtmlReporter
from coverage.misc import format_lines, CoverageException
from coverage.summary import SummaryReporter
from coverage.xml import XmlReporter

class coverage:
    """Programmatic access to Coverage.

    To use::
    
        from coverage import coverage
        
        cov = coverage()
        cov.start()
        #.. blah blah (run your code) blah blah ..
        cov.stop()
        cov.html_report(directory='covhtml')

    """

    def __init__(self, data_file=None, data_suffix=False, cover_pylib=False,
                auto_data=False, timid=False):
        """Create a new coverage measurement context.
        
        `data_file` is the base name of the data file to use, defaulting to
        ".coverage".  `data_suffix` is appended to `data_file` to create the
        final file name.  If `data_suffix` is simply True, then a suffix is
        created with the machine and process identity included.
        
        `cover_pylib` is a boolean determining whether Python code installed
        with the Python interpreter is measured.  This includes the Python
        standard library and any packages installed with the interpreter.
        
        If `auto_data` is true, then any existing data file will be read when
        coverage measurement starts, and data will be saved automatically when
        measurement stops.
        
        If `timid` is true, then a slower simpler trace function will be
        used.  This is important for some environments where manipulation of
        tracing functions make the faster more sophisticated trace function not
        operate properly.
        
        """
        from coverage import __version__
        
        self.cover_pylib = cover_pylib
        self.auto_data = auto_data
        
        self.exclude_re = ""
        self.exclude_list = []
        
        self.file_locator = FileLocator()
        
        # Timidity: for nose users, read an environment variable.  This is a
        # cheap hack, since the rest of the command line arguments aren't
        # recognized, but it solves some users' problems.
        timid = timid or ('--timid' in os.environ.get('COVERAGE_OPTIONS', ''))
        self.collector = Collector(self._should_trace, timid=timid)

        # Create the data file.
        if data_suffix:
            if not isinstance(data_suffix, basestring):
                # if data_suffix=True, use .machinename.pid
                data_suffix = ".%s.%s" % (socket.gethostname(), os.getpid())
        else:
            data_suffix = None

        self.data = CoverageData(
            basename=data_file, suffix=data_suffix,
            collector="coverage v%s" % __version__
            )

        # The default exclude pattern.
        self.exclude('# *pragma[: ]*[nN][oO] *[cC][oO][vV][eE][rR]')

        # The prefix for files considered "installed with the interpreter".
        if not self.cover_pylib:
            os_file = self.file_locator.canonical_filename(os.__file__)
            self.pylib_prefix = os.path.split(os_file)[0]

        here = self.file_locator.canonical_filename(__file__)
        self.cover_prefix = os.path.split(here)[0]

    def _should_trace(self, filename, frame):
        """Decide whether to trace execution in `filename`
        
        Returns a canonicalized filename if it should be traced, False if it
        should not.
        
        """
        if filename == '<string>':
            # There's no point in ever tracing string executions, we can't do
            # anything with the data later anyway.
            return False

        # Compiled Python files have two filenames: frame.f_code.co_filename is
        # the filename at the time the .pyc was compiled.  The second name
        # is __file__, which is where the .pyc was actually loaded from.  Since
        # .pyc files can be moved after compilation (for example, by being
        # installed), we look for __file__ in the frame and prefer it to the
        # co_filename value.
        dunder_file = frame.f_globals.get('__file__')
        if dunder_file:
            if not dunder_file.endswith(".py"):
                if dunder_file[-4:-1] == ".py":
                    dunder_file = dunder_file[:-1]
            filename = dunder_file

        canonical = self.file_locator.canonical_filename(filename)

        # If we aren't supposed to trace installed code, then check if this is
        # near the Python standard library and skip it if so.
        if not self.cover_pylib:
            if canonical.startswith(self.pylib_prefix):
                return False

        # We exclude the coverage code itself, since a little of it will be
        # measured otherwise.
        if canonical.startswith(self.cover_prefix):
            return False

        return canonical

    # To log what should_trace returns, change this to "if 1:"
    if 0:
        _real_should_trace = _should_trace
        def _should_trace(self, filename, frame):   # pylint: disable-msg=E0102
            """A logging decorator around the real _should_trace function."""
            ret = self._real_should_trace(filename, frame)
            print "should_trace: %r -> %r" % (filename, ret)
            return ret

    def use_cache(self, usecache):
        """Control the use of a data file (incorrectly called a cache).
        
        `usecache` is true or false, whether to read and write data on disk.
        
        """
        self.data.usefile(usecache)

    def load(self):
        """Load previously-collected coverage data from the data file."""
        self.collector.reset()
        self.data.read()
        
    def start(self):
        """Start measuring code coverage."""
        if self.auto_data:
            self.load()
            # Save coverage data when Python exits.
            import atexit
            atexit.register(self.save)
        self.collector.start()
        
    def stop(self):
        """Stop measuring code coverage."""
        self.collector.stop()
        self._harvest_data()

    def erase(self):
        """Erase previously-collected coverage data.
        
        This removes the in-memory data collected in this session as well as
        discarding the data file.
        
        """
        self.collector.reset()
        self.data.erase()

    def clear_exclude(self):
        """Clear the exclude list."""
        self.exclude_list = []
        self.exclude_re = ""

    def exclude(self, regex):
        """Exclude source lines from execution consideration.
        
        `regex` is a regular expression.  Lines matching this expression are
        not considered executable when reporting code coverage.  A list of
        regexes is maintained; this function adds a new regex to the list.
        Matching any of the regexes excludes a source line.
        
        """
        self.exclude_list.append(regex)
        self.exclude_re = "(" + ")|(".join(self.exclude_list) + ")"

    def get_exclude_list(self):
        """Return the list of excluded regex patterns."""
        return self.exclude_list

    def save(self):
        """Save the collected coverage data to the data file."""
        self._harvest_data()
        self.data.write()

    def combine(self):
        """Combine together a number of similarly-named coverage data files.
        
        All coverage data files whose name starts with `data_file` (from the
        coverage() constructor) will be read, and combined together into the
        current measurements.
        
        """
        self.data.combine_parallel_data()

    def _harvest_data(self):
        """Get the collected data by filename and reset the collector."""
        self.data.add_line_data(self.collector.data_points())
        self.collector.reset()

    # Backward compatibility with version 1.
    def analysis(self, morf):
        """Like `analysis2` but doesn't return excluded line numbers."""
        f, s, _, m, mf = self.analysis2(morf)
        return f, s, m, mf

    def analysis2(self, morf):
        """Analyze a module.
        
        `morf` is a module or a filename.  It will be analyzed to determine
        its coverage statistics.  The return value is a 5-tuple:
        
        * The filename for the module.
        * A list of line numbers of executable statements.
        * A list of line numbers of excluded statements.
        * A list of line numbers of statements not run (missing from execution).
        * A readable formatted string of the missing line numbers.

        The analysis uses the source file itself and the current measured
        coverage data.

        """
        code_unit = code_unit_factory(morf, self.file_locator)[0]
        st, ex, m, mf = self._analyze(code_unit)
        return code_unit.filename, st, ex, m, mf

    def _analyze(self, code_unit):
        """Analyze a single code unit.
        
        Returns a 4-tuple: (statements, excluded, missing, missing formatted).

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

    def report(self, morfs=None, show_missing=True, ignore_errors=False,
                file=None, omit_prefixes=None):     # pylint: disable-msg=W0622
        """Write a summary report to `file`.
        
        Each module in `morfs` is listed, with counts of statements, executed
        statements, missing statements, and a list of lines missed.
        
        """
        reporter = SummaryReporter(self, show_missing, ignore_errors)
        reporter.report(morfs, outfile=file, omit_prefixes=omit_prefixes)

    def annotate(self, morfs=None, directory=None, ignore_errors=False,
                    omit_prefixes=None):
        """Annotate a list of modules.
        
        Each module in `morfs` is annotated.  The source is written to a new
        file, named with a ",cover" suffix, with each line prefixed with a
        marker to indicate the coverage of the line.  Covered lines have ">",
        excluded lines have "-", and missing lines have "!".
        
        """
        reporter = AnnotateReporter(self, ignore_errors)
        reporter.report(
            morfs, directory=directory, omit_prefixes=omit_prefixes)

    def html_report(self, morfs=None, directory=None, ignore_errors=False,
                    omit_prefixes=None):
        """Generate an HTML report.
        
        """
        reporter = HtmlReporter(self, ignore_errors)
        reporter.report(
            morfs, directory=directory, omit_prefixes=omit_prefixes)

    def xml_report(self, morfs=None, ignore_errors=False, omit_prefixes=None):
        """Generate an XML report of coverage results.
        
        The report is compatible with Cobertura reports.
        
        """
        reporter = XmlReporter(self, ignore_errors)
        reporter.report(morfs, omit_prefixes=omit_prefixes)
