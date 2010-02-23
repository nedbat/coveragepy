"""Core control stuff for Coverage."""

import atexit, os, random, socket, sys

from coverage.annotate import AnnotateReporter
from coverage.backward import string_class
from coverage.codeunit import code_unit_factory, CodeUnit
from coverage.collector import Collector
from coverage.config import CoverageConfig
from coverage.data import CoverageData
from coverage.files import FileLocator
from coverage.html import HtmlReporter
from coverage.misc import bool_or_none
from coverage.results import Analysis
from coverage.summary import SummaryReporter
from coverage.xmlreport import XmlReporter

class coverage(object):
    """Programmatic access to Coverage.

    To use::

        from coverage import coverage

        cov = coverage()
        cov.start()
        #.. blah blah (run your code) blah blah ..
        cov.stop()
        cov.html_report(directory='covhtml')

    """

    def __init__(self, data_file=None, data_suffix=None, cover_pylib=None,
                auto_data=False, timid=None, branch=None, config_file=True):
        """
        `data_file` is the base name of the data file to use, defaulting to
        ".coverage".  `data_suffix` is appended (with a dot) to `data_file` to
        create the final file name.  If `data_suffix` is simply True, then a
        suffix is created with the machine and process identity included.

        `cover_pylib` is a boolean determining whether Python code installed
        with the Python interpreter is measured.  This includes the Python
        standard library and any packages installed with the interpreter.

        If `auto_data` is true, then any existing data file will be read when
        coverage measurement starts, and data will be saved automatically when
        measurement stops.

        If `timid` is true, then a slower and simpler trace function will be
        used.  This is important for some environments where manipulation of
        tracing functions breaks the faster trace function.

        If `branch` is true, then branch coverage will be measured in addition
        to the usual statement coverage.

        `config_file` determines what config file to read.  If it is a string,
        it is the name of the config file to read.  If it is True, then a
        standard file is read (".coveragerc").  If it is False, then no file is
        read.

        """
        from coverage import __version__

        # Build our configuration from a number of sources:
        # 1: defaults:
        self.config = CoverageConfig()

        # 2: from the coveragerc file:
        if config_file:
            if config_file is True:
                config_file = ".coveragerc"
            self.config.from_file(config_file)

        # 3: from environment variables:
        self.config.from_environment('COVERAGE_OPTIONS')
        env_data_file = os.environ.get('COVERAGE_FILE')
        if env_data_file:
            self.config.data_file = env_data_file

        # 4: from constructor arguments:
        self.config.from_args(
            data_file=data_file, cover_pylib=cover_pylib, timid=timid,
            branch=branch, parallel=bool_or_none(data_suffix)
            )

        self.auto_data = auto_data
        self.atexit_registered = False

        self.exclude_re = ""
        self._compile_exclude()

        self.file_locator = FileLocator()

        self.collector = Collector(
            self._should_trace, timid=self.config.timid,
            branch=self.config.branch
            )

        # Create the data file.
        if data_suffix or self.config.parallel:
            if not isinstance(data_suffix, string_class):
                # if data_suffix=True, use .machinename.pid.random
                data_suffix = "%s.%s.%06d" % (
                    socket.gethostname(), os.getpid(), random.randint(0, 99999)
                    )
        else:
            data_suffix = None

        self.data = CoverageData(
            basename=self.config.data_file, suffix=data_suffix,
            collector="coverage v%s" % __version__
            )

        # The prefix for files considered "installed with the interpreter".
        if not self.config.cover_pylib:
            # Look at where the "os" module is located.  That's the indication
            # for "installed with the interpreter".
            os_file = self.file_locator.canonical_filename(os.__file__)
            self.pylib_prefix = os.path.split(os_file)[0]

        # To avoid tracing the coverage code itself, we skip anything located
        # where we are.
        here = self.file_locator.canonical_filename(__file__)
        self.cover_prefix = os.path.split(here)[0]

    def _should_trace(self, filename, frame):
        """Decide whether to trace execution in `filename`

        This function is called from the trace function.  As each new file name
        is encountered, this function determines whether it is traced or not.

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
        if not self.config.cover_pylib:
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
            print("should_trace: %r -> %r" % (filename, ret))
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
            if not self.atexit_registered:
                atexit.register(self.save)
                self.atexit_registered = True
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
        self.config.exclude_list = []
        self.exclude_re = ""

    def exclude(self, regex):
        """Exclude source lines from execution consideration.

        `regex` is a regular expression.  Lines matching this expression are
        not considered executable when reporting code coverage.  A list of
        regexes is maintained; this function adds a new regex to the list.
        Matching any of the regexes excludes a source line.

        """
        self.config.exclude_list.append(regex)
        self._compile_exclude()

    def _compile_exclude(self):
        """Build the internal usable form of the exclude list."""
        self.exclude_re = "(" + ")|(".join(self.config.exclude_list) + ")"

    def get_exclude_list(self):
        """Return the list of excluded regex patterns."""
        return self.config.exclude_list

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
        # If the .coveragerc file specifies parallel=True, then self.data
        # already points to a suffixed data file.  This won't be right for
        # combining, so make a new self.data with no suffix.
        from coverage import __version__
        self.data = CoverageData(
            basename=self.config.data_file,
            collector="coverage v%s" % __version__
            )
        self.data.combine_parallel_data()

    def _harvest_data(self):
        """Get the collected data and reset the collector."""
        self.data.add_line_data(self.collector.get_line_data())
        self.data.add_arc_data(self.collector.get_arc_data())
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
        * A list of line numbers of statements not run (missing from
          execution).
        * A readable formatted string of the missing line numbers.

        The analysis uses the source file itself and the current measured
        coverage data.

        """
        analysis = self._analyze(morf)
        return (
            analysis.filename, analysis.statements, analysis.excluded,
            analysis.missing, analysis.missing_formatted()
            )

    def _analyze(self, it):
        """Analyze a single morf or code unit.

        Returns an `Analysis` object.

        """
        if not isinstance(it, CodeUnit):
            it = code_unit_factory(it, self.file_locator)[0]

        return Analysis(self, it)

    def report(self, morfs=None, show_missing=True, ignore_errors=None,
                file=None, omit_prefixes=None):     # pylint: disable-msg=W0622
        """Write a summary report to `file`.

        Each module in `morfs` is listed, with counts of statements, executed
        statements, missing statements, and a list of lines missed.

        """
        self.config.from_args(
            ignore_errors=ignore_errors,
            omit_prefixes=omit_prefixes
            )
        reporter = SummaryReporter(
            self, show_missing, self.config.ignore_errors
            )
        reporter.report(
            morfs, outfile=file, omit_prefixes=self.config.omit_prefixes
            )

    def annotate(self, morfs=None, directory=None, ignore_errors=None,
                    omit_prefixes=None):
        """Annotate a list of modules.

        Each module in `morfs` is annotated.  The source is written to a new
        file, named with a ",cover" suffix, with each line prefixed with a
        marker to indicate the coverage of the line.  Covered lines have ">",
        excluded lines have "-", and missing lines have "!".

        """
        self.config.from_args(
            ignore_errors=ignore_errors,
            omit_prefixes=omit_prefixes
            )
        reporter = AnnotateReporter(self, self.config.ignore_errors)
        reporter.report(
            morfs, directory=directory, omit_prefixes=self.config.omit_prefixes
            )

    def html_report(self, morfs=None, directory=None, ignore_errors=None,
                    omit_prefixes=None):
        """Generate an HTML report.

        """
        self.config.from_args(
            ignore_errors=ignore_errors,
            omit_prefixes=omit_prefixes,
            html_dir=directory,
            )
        reporter = HtmlReporter(self, self.config.ignore_errors)
        reporter.report(
            morfs, directory=self.config.html_dir,
            omit_prefixes=self.config.omit_prefixes
            )

    def xml_report(self, morfs=None, outfile=None, ignore_errors=None,
                    omit_prefixes=None):
        """Generate an XML report of coverage results.

        The report is compatible with Cobertura reports.

        Each module in `morfs` is included in the report.  `outfile` is the
        path to write the file to, "-" will write to stdout.

        """
        self.config.from_args(
            ignore_errors=ignore_errors,
            omit_prefixes=omit_prefixes,
            xml_output=outfile,
            )
        file_to_close = None
        if self.config.xml_output:
            if self.config.xml_output == '-':
                outfile = sys.stdout
            else:
                outfile = open(self.config.xml_output, "w")
                file_to_close = outfile
        try:
            reporter = XmlReporter(self, self.config.ignore_errors)
            reporter.report(
                morfs, omit_prefixes=self.config.omit_prefixes, outfile=outfile
                )
        finally:
            if file_to_close:
                file_to_close.close()

    def sysinfo(self):
        """Return a list of (key, value) pairs showing internal information."""

        import coverage as covmod
        import platform, re

        info = [
            ('version', covmod.__version__),
            ('coverage', covmod.__file__),
            ('cover_prefix', self.cover_prefix),
            ('pylib_prefix', self.pylib_prefix),
            ('tracer', self.collector.tracer_name()),
            ('data_path', self.data.filename),
            ('python', sys.version.replace('\n', '')),
            ('platform', platform.platform()),
            ('cwd', os.getcwd()),
            ('path', sys.path),
            ('environment', [
                ("%s = %s" % (k, v)) for k, v in os.environ.items()
                    if re.search("^COV|^PY", k)
                ]),
            ]
        return info


def process_startup():
    """Call this at Python startup to perhaps measure coverage.

    If the environment variable COVERAGE_PROCESS_START is defined, coverage
    measurement is started.  The value of the variable is the config file
    to use.

    There are two ways to configure your Python installation to invoke this
    function when Python starts:

    #. Create or append to sitecustomize.py to add these lines::

        import coverage
        coverage.process_startup()

    #. Create a .pth file in your Python installation containing::

        import coverage; coverage.process_startup()

    """
    cps = os.environ.get("COVERAGE_PROCESS_START")
    if cps:
        cov = coverage(config_file=cps, auto_data=True)
        if os.environ.get("COVERAGE_COVERAGE"):
            # Measuring coverage within coverage.py takes yet more trickery.
            cov.cover_prefix = "Please measure coverage.py!"
        cov.start()
