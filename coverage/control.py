"""Core control stuff for Coverage."""

import atexit, os, platform, random, socket, sys

from coverage.annotate import AnnotateReporter
from coverage.backward import string_class, iitems
from coverage.codeunit import code_unit_factory, CodeUnit, PythonCodeUnit
from coverage.collector import Collector
from coverage.config import CoverageConfig
from coverage.data import CoverageData
from coverage.debug import DebugControl
from coverage.plugin import Plugins, plugin_implements
from coverage.files import FileLocator, TreeMatcher, FnmatchMatcher
from coverage.files import PathAliases, find_python_files, prep_patterns
from coverage.html import HtmlReporter
from coverage.misc import CoverageException, bool_or_none, join_regex
from coverage.misc import file_be_gone
from coverage.results import Analysis, Numbers
from coverage.summary import SummaryReporter
from coverage.xmlreport import XmlReporter


# Pypy has some unusual stuff in the "stdlib".  Consider those locations
# when deciding where the stdlib is.
try:
    import _structseq       # pylint: disable=F0401
except ImportError:
    _structseq = None


class Coverage(object):
    """Programmatic access to coverage.py.

    To use::

        from coverage import coverage

        cov = Coverage()
        cov.start()
        #.. call your code ..
        cov.stop()
        cov.html_report(directory='covhtml')

    """
    def __init__(self, data_file=None, data_suffix=None, cover_pylib=None,
                auto_data=False, timid=None, branch=None, config_file=True,
                source=None, omit=None, include=None, debug=None,
                debug_file=None, concurrency=None, plugins=None):
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

        `source` is a list of file paths or package names.  Only code located
        in the trees indicated by the file paths or package names will be
        measured.

        `include` and `omit` are lists of filename patterns. Files that match
        `include` will be measured, files that match `omit` will not.  Each
        will also accept a single string argument.

        `debug` is a list of strings indicating what debugging information is
        desired. `debug_file` is the file to write debug messages to,
        defaulting to stderr.

        `concurrency` is a string indicating the concurrency library being used
        in the measured code.  Without this, coverage.py will get incorrect
        results.  Valid strings are "greenlet", "eventlet", "gevent", or
        "thread" (the default).

        `plugins` TODO.

        """
        from coverage import __version__

        # A record of all the warnings that have been issued.
        self._warnings = []

        # Build our configuration from a number of sources:
        # 1: defaults:
        self.config = CoverageConfig()

        # 2: from the .coveragerc or setup.cfg file:
        if config_file:
            did_read_rc = should_read_setupcfg = False
            if config_file is True:
                config_file = ".coveragerc"
                should_read_setupcfg = True
            try:
                did_read_rc = self.config.from_file(config_file)
            except ValueError as err:
                raise CoverageException(
                    "Couldn't read config file %s: %s" % (config_file, err)
                    )

            if not did_read_rc and should_read_setupcfg:
                self.config.from_file("setup.cfg", section_prefix="coverage:")

        # 3: from environment variables:
        env_data_file = os.environ.get('COVERAGE_FILE')
        if env_data_file:
            self.config.data_file = env_data_file

        # 4: from constructor arguments:
        self.config.from_args(
            data_file=data_file, cover_pylib=cover_pylib, timid=timid,
            branch=branch, parallel=bool_or_none(data_suffix),
            source=source, omit=omit, include=include, debug=debug,
            concurrency=concurrency, plugins=plugins,
            )

        # Create and configure the debugging controller.
        self.debug = DebugControl(self.config.debug, debug_file or sys.stderr)

        # Load plugins
        self.plugins = Plugins.load_plugins(self.config.plugins, self.config)

        self.trace_judges = []
        for plugin in self.plugins:
            if plugin_implements(plugin, "trace_judge"):
                self.trace_judges.append(plugin)
        self.trace_judges.append(None)      # The Python case.

        self.auto_data = auto_data

        # _exclude_re is a dict mapping exclusion list names to compiled
        # regexes.
        self._exclude_re = {}
        self._exclude_regex_stale()

        self.file_locator = FileLocator()

        # The source argument can be directories or package names.
        self.source = []
        self.source_pkgs = []
        for src in self.config.source or []:
            if os.path.exists(src):
                self.source.append(self.file_locator.canonical_filename(src))
            else:
                self.source_pkgs.append(src)

        self.omit = prep_patterns(self.config.omit)
        self.include = prep_patterns(self.config.include)

        self.collector = Collector(
            should_trace=self._should_trace,
            check_include=self._tracing_check_include_omit_etc,
            timid=self.config.timid,
            branch=self.config.branch,
            warn=self._warn,
            concurrency=self.config.concurrency,
            )

        # Suffixes are a bit tricky.  We want to use the data suffix only when
        # collecting data, not when combining data.  So we save it as
        # `self.run_suffix` now, and promote it to `self.data_suffix` if we
        # find that we are collecting data later.
        if data_suffix or self.config.parallel:
            if not isinstance(data_suffix, string_class):
                # if data_suffix=True, use .machinename.pid.random
                data_suffix = True
        else:
            data_suffix = None
        self.data_suffix = None
        self.run_suffix = data_suffix

        # Create the data file.  We do this at construction time so that the
        # data file will be written into the directory where the process
        # started rather than wherever the process eventually chdir'd to.
        self.data = CoverageData(
            basename=self.config.data_file,
            collector="coverage v%s" % __version__,
            debug=self.debug,
            )

        # The dirs for files considered "installed with the interpreter".
        self.pylib_dirs = set()
        if not self.config.cover_pylib:
            # Look at where some standard modules are located. That's the
            # indication for "installed with the interpreter". In some
            # environments (virtualenv, for example), these modules may be
            # spread across a few locations. Look at all the candidate modules
            # we've imported, and take all the different ones.
            for m in (atexit, os, platform, random, socket, _structseq):
                if m is not None and hasattr(m, "__file__"):
                    self.pylib_dirs.add(self._canonical_dir(m))

        # To avoid tracing the coverage code itself, we skip anything located
        # where we are.
        self.cover_dir = self._canonical_dir(__file__)

        # The matchers for _should_trace.
        self.source_match = None
        self.pylib_match = self.cover_match = None
        self.include_match = self.omit_match = None

        # Set the reporting precision.
        Numbers.set_precision(self.config.precision)

        # Is it ok for no data to be collected?
        self._warn_no_data = True
        self._warn_unimported_source = True

        # State machine variables:
        # Have we started collecting and not stopped it?
        self._started = False
        # Have we measured some data and not harvested it?
        self._measured = False

        atexit.register(self._atexit)

    def _canonical_dir(self, morf):
        """Return the canonical directory of the module or file `morf`."""
        morf_filename = PythonCodeUnit(morf, self.file_locator).filename
        return os.path.split(morf_filename)[0]

    def _source_for_file(self, filename):
        """Return the source file for `filename`."""
        if not filename.endswith(".py"):
            if filename[-4:-1] == ".py":
                filename = filename[:-1]
            elif filename.endswith("$py.class"): # jython
                filename = filename[:-9] + ".py"
        return filename

    def _should_trace_with_reason(self, filename, frame):
        """Decide whether to trace execution in `filename`, with a reason.

        This function is called from the trace function.  As each new file name
        is encountered, this function determines whether it is traced or not.

        Returns a FileDisposition object.

        """
        disp = FileDisposition(filename)
        def nope(disp, reason):
            disp.trace = False
            disp.reason = reason
            return disp

        self._check_for_packages()

        # Compiled Python files have two filenames: frame.f_code.co_filename is
        # the filename at the time the .pyc was compiled.  The second name is
        # __file__, which is where the .pyc was actually loaded from.  Since
        # .pyc files can be moved after compilation (for example, by being
        # installed), we look for __file__ in the frame and prefer it to the
        # co_filename value.
        dunder_file = frame.f_globals.get('__file__')
        if dunder_file:
            filename = self._source_for_file(dunder_file)

        if not filename:
            # Empty string is pretty useless
            return nope(disp, "empty string isn't a filename")

        if filename.startswith('memory:'):
            return nope(disp, "memory isn't traceable")

        if filename.startswith('<'):
            # Lots of non-file execution is represented with artificial
            # filenames like "<string>", "<doctest readme.txt[0]>", or
            # "<exec_function>".  Don't ever trace these executions, since we
            # can't do anything with the data later anyway.
            return nope(disp, "not a real filename")

        # Jython reports the .class file to the tracer, use the source file.
        if filename.endswith("$py.class"):
            filename = filename[:-9] + ".py"

        canonical = self.file_locator.canonical_filename(filename)
        disp.canonical_filename = canonical

        # Try the plugins, see if they have an opinion about the file.
        for plugin in self.trace_judges:
            if plugin:
                plugin.trace_judge(disp)
            else:
                disp.trace = True
                disp.source_filename = canonical
            if disp.trace:
                disp.plugin = plugin

                if disp.check_filters:
                    reason = self._check_include_omit_etc(disp.source_filename)
                    if reason:
                        nope(disp, reason)

                return disp

        return nope(disp, "no plugin found")  # TODO: a test that causes this.

    def _check_include_omit_etc(self, filename):
        """Check a filename against the include, omit, etc, rules.

        Returns a string or None.  String means, don't trace, and is the reason
        why.  None means no reason found to not trace.

        """
        # If the user specified source or include, then that's authoritative
        # about the outer bound of what to measure and we don't have to apply
        # any canned exclusions. If they didn't, then we have to exclude the
        # stdlib and coverage.py directories.
        if self.source_match:
            if not self.source_match.match(filename):
                return "falls outside the --source trees"
        elif self.include_match:
            if not self.include_match.match(filename):
                return "falls outside the --include trees"
        else:
            # If we aren't supposed to trace installed code, then check if this
            # is near the Python standard library and skip it if so.
            if self.pylib_match and self.pylib_match.match(filename):
                return "is in the stdlib"

            # We exclude the coverage code itself, since a little of it will be
            # measured otherwise.
            if self.cover_match and self.cover_match.match(filename):
                return "is part of coverage.py"

        # Check the file against the omit pattern.
        if self.omit_match and self.omit_match.match(filename):
            return "is inside an --omit pattern"

        # No reason found to skip this file.
        return None

    def _should_trace(self, filename, frame):
        """Decide whether to trace execution in `filename`.

        Calls `_should_trace_with_reason`, and returns the FileDisposition.

        """
        disp = self._should_trace_with_reason(filename, frame)
        if self.debug.should('trace'):
            self.debug.write(disp.debug_message())
        return disp

    def _tracing_check_include_omit_etc(self, filename):
        """Check a filename against the include, omit, etc, rules, and say so.

        Returns a boolean: True if the file should be traced, False if not.

        """
        reason = self._check_include_omit_etc(filename)
        if self.debug.should('trace'):
            if not reason:
                msg = "Tracing %r" % (filename,)
            else:
                msg = "Not tracing %r: %s" % (filename, reason)
            self.debug.write(msg)

        return not reason

    def _warn(self, msg):
        """Use `msg` as a warning."""
        self._warnings.append(msg)
        sys.stderr.write("Coverage.py warning: %s\n" % msg)

    def _check_for_packages(self):
        """Update the source_match matcher with latest imported packages."""
        # Our self.source_pkgs attribute is a list of package names we want to
        # measure.  Each time through here, we see if we've imported any of
        # them yet.  If so, we add its file to source_match, and we don't have
        # to look for that package any more.
        if self.source_pkgs:
            found = []
            for pkg in self.source_pkgs:
                try:
                    mod = sys.modules[pkg]
                except KeyError:
                    continue

                found.append(pkg)

                try:
                    pkg_file = mod.__file__
                except AttributeError:
                    pkg_file = None
                else:
                    d, f = os.path.split(pkg_file)
                    if f.startswith('__init__'):
                        # This is actually a package, return the directory.
                        pkg_file = d
                    else:
                        pkg_file = self._source_for_file(pkg_file)
                    pkg_file = self.file_locator.canonical_filename(pkg_file)
                    if not os.path.exists(pkg_file):
                        pkg_file = None

                if pkg_file:
                    self.source.append(pkg_file)
                    self.source_match.add(pkg_file)
                else:
                    self._warn("Module %s has no Python source." % pkg)

            for pkg in found:
                self.source_pkgs.remove(pkg)

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
        """Start measuring code coverage.

        Coverage measurement actually occurs in functions called after `start`
        is invoked.  Statements in the same scope as `start` won't be measured.

        Once you invoke `start`, you must also call `stop` eventually, or your
        process might not shut down cleanly.

        """
        if self.run_suffix:
            # Calling start() means we're running code, so use the run_suffix
            # as the data_suffix when we eventually save the data.
            self.data_suffix = self.run_suffix
        if self.auto_data:
            self.load()

        # Create the matchers we need for _should_trace
        if self.source or self.source_pkgs:
            self.source_match = TreeMatcher(self.source)
        else:
            if self.cover_dir:
                self.cover_match = TreeMatcher([self.cover_dir])
            if self.pylib_dirs:
                self.pylib_match = TreeMatcher(self.pylib_dirs)
        if self.include:
            self.include_match = FnmatchMatcher(self.include)
        if self.omit:
            self.omit_match = FnmatchMatcher(self.omit)

        # The user may want to debug things, show info if desired.
        if self.debug.should('config'):
            self.debug.write("Configuration values:")
            config_info = sorted(self.config.__dict__.items())
            self.debug.write_formatted_info(config_info)

        if self.debug.should('sys'):
            self.debug.write("Debugging info:")
            self.debug.write_formatted_info(self.sysinfo())

        self.collector.start()
        self._started = True
        self._measured = True

    def stop(self):
        """Stop measuring code coverage."""
        self._started = False
        self.collector.stop()

    def _atexit(self):
        """Clean up on process shutdown."""
        if self._started:
            self.stop()
        if self.auto_data:
            self.save()

    def erase(self):
        """Erase previously-collected coverage data.

        This removes the in-memory data collected in this session as well as
        discarding the data file.

        """
        self.collector.reset()
        self.data.erase()

    def clear_exclude(self, which='exclude'):
        """Clear the exclude list."""
        setattr(self.config, which + "_list", [])
        self._exclude_regex_stale()

    def exclude(self, regex, which='exclude'):
        """Exclude source lines from execution consideration.

        A number of lists of regular expressions are maintained.  Each list
        selects lines that are treated differently during reporting.

        `which` determines which list is modified.  The "exclude" list selects
        lines that are not considered executable at all.  The "partial" list
        indicates lines with branches that are not taken.

        `regex` is a regular expression.  The regex is added to the specified
        list.  If any of the regexes in the list is found in a line, the line
        is marked for special treatment during reporting.

        """
        excl_list = getattr(self.config, which + "_list")
        excl_list.append(regex)
        self._exclude_regex_stale()

    def _exclude_regex_stale(self):
        """Drop all the compiled exclusion regexes, a list was modified."""
        self._exclude_re.clear()

    def _exclude_regex(self, which):
        """Return a compiled regex for the given exclusion list."""
        if which not in self._exclude_re:
            excl_list = getattr(self.config, which + "_list")
            self._exclude_re[which] = join_regex(excl_list)
        return self._exclude_re[which]

    def get_exclude_list(self, which='exclude'):
        """Return a list of excluded regex patterns.

        `which` indicates which list is desired.  See `exclude` for the lists
        that are available, and their meaning.

        """
        return getattr(self.config, which + "_list")

    def save(self):
        """Save the collected coverage data to the data file."""
        data_suffix = self.data_suffix
        if data_suffix is True:
            # If data_suffix was a simple true value, then make a suffix with
            # plenty of distinguishing information.  We do this here in
            # `save()` at the last minute so that the pid will be correct even
            # if the process forks.
            extra = ""
            if _TEST_NAME_FILE:                             # pragma: debugging
                with open(_TEST_NAME_FILE) as f:
                    test_name = f.read()
                extra = "." + test_name
            data_suffix = "%s%s.%s.%06d" % (
                socket.gethostname(), extra, os.getpid(),
                random.randint(0, 999999)
                )

        self._harvest_data()
        self.data.write(suffix=data_suffix)

    def combine(self):
        """Combine together a number of similarly-named coverage data files.

        All coverage data files whose name starts with `data_file` (from the
        coverage() constructor) will be read, and combined together into the
        current measurements.

        """
        aliases = None
        if self.config.paths:
            aliases = PathAliases(self.file_locator)
            for paths in self.config.paths.values():
                result = paths[0]
                for pattern in paths[1:]:
                    aliases.add(pattern, result)
        self.data.combine_parallel_data(aliases=aliases)

    def _harvest_data(self):
        """Get the collected data and reset the collector.

        Also warn about various problems collecting data.

        """
        if not self._measured:
            return

        # TODO: seems like this parallel structure is getting kinda old...
        self.data.add_line_data(self.collector.get_line_data())
        self.data.add_arc_data(self.collector.get_arc_data())
        self.data.add_plugin_data(self.collector.get_plugin_data())
        self.collector.reset()

        # If there are still entries in the source_pkgs list, then we never
        # encountered those packages.
        if self._warn_unimported_source:
            for pkg in self.source_pkgs:
                self._warn("Module %s was never imported." % pkg)

        # Find out if we got any data.
        summary = self.data.summary()
        if not summary and self._warn_no_data:
            self._warn("No data was collected.")

        # Find files that were never executed at all.
        for src in self.source:
            for py_file in find_python_files(src):
                py_file = self.file_locator.canonical_filename(py_file)

                if self.omit_match and self.omit_match.match(py_file):
                    # Turns out this file was omitted, so don't pull it back
                    # in as unexecuted.
                    continue

                self.data.touch_file(py_file)

        self._measured = False

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
            analysis.filename,
            sorted(analysis.statements),
            sorted(analysis.excluded),
            sorted(analysis.missing),
            analysis.missing_formatted(),
            )

    def _analyze(self, it):
        """Analyze a single morf or code unit.

        Returns an `Analysis` object.

        """
        def get_plugin(filename):
            """For code_unit_factory to use to find the plugin for a file."""
            plugin = None
            plugin_name = self.data.plugin_data().get(filename)
            if plugin_name:
                plugin = self.plugins.get(plugin_name)
            return plugin

        self._harvest_data()
        if not isinstance(it, CodeUnit):
            it = code_unit_factory(it, self.file_locator, get_plugin)[0]

        return Analysis(self, it)

    def report(self, morfs=None, show_missing=True, ignore_errors=None,
                file=None,                          # pylint: disable=W0622
                omit=None, include=None
                ):
        """Write a summary report to `file`.

        Each module in `morfs` is listed, with counts of statements, executed
        statements, missing statements, and a list of lines missed.

        `include` is a list of filename patterns.  Modules whose filenames
        match those patterns will be included in the report. Modules matching
        `omit` will not be included in the report.

        Returns a float, the total percentage covered.

        """
        self._harvest_data()
        self.config.from_args(
            ignore_errors=ignore_errors, omit=omit, include=include,
            show_missing=show_missing,
            )
        reporter = SummaryReporter(self, self.config)
        return reporter.report(morfs, outfile=file)

    def annotate(self, morfs=None, directory=None, ignore_errors=None,
                    omit=None, include=None):
        """Annotate a list of modules.

        Each module in `morfs` is annotated.  The source is written to a new
        file, named with a ",cover" suffix, with each line prefixed with a
        marker to indicate the coverage of the line.  Covered lines have ">",
        excluded lines have "-", and missing lines have "!".

        See `coverage.report()` for other arguments.

        """
        self._harvest_data()
        self.config.from_args(
            ignore_errors=ignore_errors, omit=omit, include=include
            )
        reporter = AnnotateReporter(self, self.config)
        reporter.report(morfs, directory=directory)

    def html_report(self, morfs=None, directory=None, ignore_errors=None,
                    omit=None, include=None, extra_css=None, title=None):
        """Generate an HTML report.

        The HTML is written to `directory`.  The file "index.html" is the
        overview starting point, with links to more detailed pages for
        individual modules.

        `extra_css` is a path to a file of other CSS to apply on the page.
        It will be copied into the HTML directory.

        `title` is a text string (not HTML) to use as the title of the HTML
        report.

        See `coverage.report()` for other arguments.

        Returns a float, the total percentage covered.

        """
        self._harvest_data()
        self.config.from_args(
            ignore_errors=ignore_errors, omit=omit, include=include,
            html_dir=directory, extra_css=extra_css, html_title=title,
            )
        reporter = HtmlReporter(self, self.config)
        return reporter.report(morfs)

    def xml_report(self, morfs=None, outfile=None, ignore_errors=None,
                    omit=None, include=None):
        """Generate an XML report of coverage results.

        The report is compatible with Cobertura reports.

        Each module in `morfs` is included in the report.  `outfile` is the
        path to write the file to, "-" will write to stdout.

        See `coverage.report()` for other arguments.

        Returns a float, the total percentage covered.

        """
        self._harvest_data()
        self.config.from_args(
            ignore_errors=ignore_errors, omit=omit, include=include,
            xml_output=outfile,
            )
        file_to_close = None
        delete_file = False
        if self.config.xml_output:
            if self.config.xml_output == '-':
                outfile = sys.stdout
            else:
                # Ensure that the output directory is created; done here
                # because this report pre-opens the output file.
                # HTMLReport does this using the Report plumbing because
                # its task is more complex, being multiple files.
                output_dir = os.path.dirname(self.config.xml_output)
                if output_dir and not os.path.isdir(output_dir):
                    os.makedirs(output_dir)
                outfile = open(self.config.xml_output, "w")
                file_to_close = outfile
        try:
            reporter = XmlReporter(self, self.config)
            return reporter.report(morfs, outfile=outfile)
        except CoverageException:
            delete_file = True
            raise
        finally:
            if file_to_close:
                file_to_close.close()
                if delete_file:
                    file_be_gone(self.config.xml_output)

    def sysinfo(self):
        """Return a list of (key, value) pairs showing internal information."""

        import coverage as covmod

        try:
            implementation = platform.python_implementation()
        except AttributeError:
            implementation = "unknown"

        info = [
            ('version', covmod.__version__),
            ('coverage', covmod.__file__),
            ('cover_dir', self.cover_dir),
            ('pylib_dirs', self.pylib_dirs),
            ('tracer', self.collector.tracer_name()),
            ('config_files', self.config.attempted_config_files),
            ('configs_read', self.config.config_files),
            ('data_path', self.data.filename),
            ('python', sys.version.replace('\n', '')),
            ('platform', platform.platform()),
            ('implementation', implementation),
            ('executable', sys.executable),
            ('cwd', os.getcwd()),
            ('path', sys.path),
            ('environment', sorted(
                ("%s = %s" % (k, v)) for k, v in iitems(os.environ)
                    if k.startswith(("COV", "PY"))
                )),
            ('command_line', " ".join(getattr(sys, 'argv', ['???']))),
            ]
        if self.source_match:
            info.append(('source_match', self.source_match.info()))
        if self.include_match:
            info.append(('include_match', self.include_match.info()))
        if self.omit_match:
            info.append(('omit_match', self.omit_match.info()))
        if self.cover_match:
            info.append(('cover_match', self.cover_match.info()))
        if self.pylib_match:
            info.append(('pylib_match', self.pylib_match.info()))

        return info


class FileDisposition(object):
    """A simple object for noting a number of details of files to trace."""
    def __init__(self, original_filename):
        self.original_filename = original_filename
        self.canonical_filename = original_filename
        self.source_filename = None
        self.check_filters = True
        self.trace = False
        self.reason = ""
        self.plugin = None

    def debug_message(self):
        """Produce a debugging message explaining the outcome."""
        if self.trace:
            msg = "Tracing %r" % (self.original_filename,)
        else:
            msg = "Not tracing %r: %s" % (self.original_filename, self.reason)
        return msg


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
        cov = Coverage(config_file=cps, auto_data=True)
        cov.start()
        cov._warn_no_data = False
        cov._warn_unimported_source = False


# A hack for debugging testing in subprocesses.
_TEST_NAME_FILE = "" #"/tmp/covtest.txt"
