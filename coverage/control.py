# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Central control stuff for coverage.py."""

from __future__ import annotations

import atexit
import collections
import contextlib
import functools
import os
import os.path
import platform
import signal
import sys
import threading
import time
import warnings

from types import FrameType
from typing import cast, Any, Callable, IO, Union
from collections.abc import Iterable, Iterator

from coverage import env
from coverage.annotate import AnnotateReporter
from coverage.collector import Collector
from coverage.config import CoverageConfig, read_coverage_config
from coverage.context import should_start_context_test_function, combine_context_switchers
from coverage.core import Core, CTRACER_FILE
from coverage.data import CoverageData, combine_parallel_data
from coverage.debug import (
    DebugControl, NoDebugging, short_stack, write_formatted_info, relevant_environment_display,
)
from coverage.disposition import disposition_debug_msg
from coverage.exceptions import ConfigError, CoverageException, CoverageWarning, PluginError
from coverage.files import PathAliases, abs_file, relative_filename, set_relative_directory
from coverage.html import HtmlReporter
from coverage.inorout import InOrOut
from coverage.jsonreport import JsonReporter
from coverage.lcovreport import LcovReporter
from coverage.misc import bool_or_none, join_regex
from coverage.misc import DefaultValue, ensure_dir_for_file, isolate_module
from coverage.multiproc import patch_multiprocessing
from coverage.patch import apply_patches
from coverage.plugin import FileReporter
from coverage.plugin_support import Plugins, TCoverageInit
from coverage.python import PythonFileReporter
from coverage.report import SummaryReporter
from coverage.report_core import render_report
from coverage.results import Analysis, analysis_from_file_reporter
from coverage.types import (
    FilePath, TConfigurable, TConfigSectionIn, TConfigValueIn, TConfigValueOut,
    TFileDisposition, TLineNo, TMorf
)
from coverage.xmlreport import XmlReporter

os = isolate_module(os)

@contextlib.contextmanager
def override_config(cov: Coverage, **kwargs: TConfigValueIn) -> Iterator[None]:
    """Temporarily tweak the configuration of `cov`.

    The arguments are applied to `cov.config` with the `from_args` method.
    At the end of the with-statement, the old configuration is restored.
    """
    original_config = cov.config
    cov.config = cov.config.copy()
    try:
        cov.config.from_args(**kwargs)
        yield
    finally:
        cov.config = original_config


DEFAULT_DATAFILE = DefaultValue("MISSING")
_DEFAULT_DATAFILE = DEFAULT_DATAFILE  # Just in case, for backwards compatibility

class Coverage(TConfigurable):
    """Programmatic access to coverage.py.

    To use::

        from coverage import Coverage

        cov = Coverage()
        cov.start()
        #.. call your code ..
        cov.stop()
        cov.html_report(directory="covhtml")

    A context manager is available to do the same thing::

        cov = Coverage()
        with cov.collect():
            #.. call your code ..
        cov.html_report(directory="covhtml")

    Note: in keeping with Python custom, names starting with underscore are
    not part of the public API. They might stop working at any point.  Please
    limit yourself to documented methods to avoid problems.

    Methods can raise any of the exceptions described in :ref:`api_exceptions`.

    """

    # The stack of started Coverage instances.
    _instances: list[Coverage] = []

    @classmethod
    def current(cls) -> Coverage | None:
        """Get the latest started `Coverage` instance, if any.

        Returns: a `Coverage` instance, or None.

        .. versionadded:: 5.0

        """
        if cls._instances:
            return cls._instances[-1]
        else:
            return None

    def __init__(                       # pylint: disable=too-many-arguments
        self,
        data_file: FilePath | DefaultValue | None = DEFAULT_DATAFILE,
        data_suffix: str | bool | None = None,
        cover_pylib: bool | None = None,
        auto_data: bool = False,
        timid: bool | None = None,
        branch: bool | None = None,
        config_file: FilePath | bool = True,
        source: Iterable[str] | None = None,
        source_pkgs: Iterable[str] | None = None,
        source_dirs: Iterable[str] | None = None,
        omit: str | Iterable[str] | None = None,
        include: str | Iterable[str] | None = None,
        debug: Iterable[str] | None = None,
        concurrency: str | Iterable[str] | None = None,
        check_preimported: bool = False,
        context: str | None = None,
        messages: bool = False,
        plugins: Iterable[Callable[..., None]] | None = None,
    ) -> None:
        """
        Many of these arguments duplicate and override values that can be
        provided in a configuration file.  Parameters that are missing here
        will use values from the config file.

        `data_file` is the base name of the data file to use. The config value
        defaults to ".coverage".  None can be provided to prevent writing a data
        file.  `data_suffix` is appended (with a dot) to `data_file` to create
        the final file name.  If `data_suffix` is simply True, then a suffix is
        created with the machine and process identity included.

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

        `config_file` determines what configuration file to read:

            * If it is ".coveragerc", it is interpreted as if it were True,
              for backward compatibility.

            * If it is a string, it is the name of the file to read.  If the
              file can't be read, it is an error.

            * If it is True, then a few standard files names are tried
              (".coveragerc", "setup.cfg", "tox.ini").  It is not an error for
              these files to not be found.

            * If it is False, then no configuration file is read.

        `source` is a list of file paths or package names.  Only code located
        in the trees indicated by the file paths or package names will be
        measured.

        `source_pkgs` is a list of package names. It works the same as
        `source`, but can be used to name packages where the name can also be
        interpreted as a file path.

        `source_dirs` is a list of file paths. It works the same as
        `source`, but raises an error if the path doesn't exist, rather
        than being treated as a package name.

        `include` and `omit` are lists of file name patterns. Files that match
        `include` will be measured, files that match `omit` will not.  Each
        will also accept a single string argument.

        `debug` is a list of strings indicating what debugging information is
        desired.

        `concurrency` is a string indicating the concurrency library being used
        in the measured code.  Without this, coverage.py will get incorrect
        results if these libraries are in use.  Valid strings are "greenlet",
        "eventlet", "gevent", "multiprocessing", or "thread" (the default).
        This can also be a list of these strings.

        If `check_preimported` is true, then when coverage is started, the
        already-imported files will be checked to see if they should be
        measured by coverage.  Importing measured files before coverage is
        started can mean that code is missed.

        `context` is a string to use as the :ref:`static context
        <static_contexts>` label for collected data.

        If `messages` is true, some messages will be printed to stdout
        indicating what is happening.

        If `plugins` are passed, they are an iterable of function objects
        accepting a `reg` object to register plugins, as described in
        :ref:`api_plugin`.  When they are provided, they will override the
        plugins found in the coverage configuration file.

        .. versionadded:: 4.0
            The `concurrency` parameter.

        .. versionadded:: 4.2
            The `concurrency` parameter can now be a list of strings.

        .. versionadded:: 5.0
            The `check_preimported` and `context` parameters.

        .. versionadded:: 5.3
            The `source_pkgs` parameter.

        .. versionadded:: 6.0
            The `messages` parameter.

        .. versionadded:: 7.7
            The `plugins` parameter.

        .. versionadded:: 7.8
            The `source_dirs` parameter.
        """
        # Start self.config as a usable default configuration. It will soon be
        # replaced with the real configuration.
        self.config = CoverageConfig()

        # data_file=None means no disk file at all. data_file missing means
        # use the value from the config file.
        self._no_disk = data_file is None
        if isinstance(data_file, DefaultValue):
            data_file = None
        if data_file is not None:
            data_file = os.fspath(data_file)

        # This is injectable by tests.
        self._debug_file: IO[str] | None = None

        self._auto_load = self._auto_save = auto_data
        self._data_suffix_specified = data_suffix

        # Is it ok for no data to be collected?
        self._warn_no_data = True
        self._warn_unimported_source = True
        self._warn_preimported_source = check_preimported
        self._no_warn_slugs: set[str] = set()
        self._messages = messages

        # If we're invoked from a .pth file, we shouldn't try to make another one.
        self._make_pth_file = True

        # A record of all the warnings that have been issued.
        self._warnings: list[str] = []

        # Other instance attributes, set with placebos or placeholders.
        # More useful objects will be created later.
        self._debug: DebugControl = NoDebugging()
        self._inorout: InOrOut | None = None
        self._plugins: Plugins = Plugins()
        self._plugin_override = cast(Union[Iterable[TCoverageInit], None], plugins)
        self._data: CoverageData | None = None
        self._core: Core | None = None
        self._collector: Collector | None = None
        self._metacov = False

        self._file_mapper: Callable[[str], str] = abs_file
        self._data_suffix = self._run_suffix = None
        self._exclude_re: dict[str, str] = {}
        self._old_sigterm: Callable[[int, FrameType | None], Any] | None = None

        # State machine variables:
        # Have we initialized everything?
        self._inited = False
        self._inited_for_start = False
        # Have we started collecting and not stopped it?
        self._started = False
        # Should we write the debug output?
        self._should_write_debug = True

        # Build our configuration from a number of sources.
        if not isinstance(config_file, bool):
            config_file = os.fspath(config_file)
        self.config = read_coverage_config(
            config_file=config_file,
            warn=self._warn,
            data_file=data_file,
            cover_pylib=cover_pylib,
            timid=timid,
            branch=branch,
            parallel=bool_or_none(data_suffix),
            source=source,
            source_pkgs=source_pkgs,
            source_dirs=source_dirs,
            run_omit=omit,
            run_include=include,
            debug=debug,
            report_omit=omit,
            report_include=include,
            concurrency=concurrency,
            context=context,
        )

        # If we have subprocess measurement happening automatically, then we
        # want any explicit creation of a Coverage object to mean, this process
        # is already coverage-aware, so don't auto-measure it.  By now, the
        # auto-creation of a Coverage object has already happened.  But we can
        # find it and tell it not to save its data.
        if not env.METACOV:
            _prevent_sub_process_measurement()

    def _init(self) -> None:
        """Set all the initial state.

        This is called by the public methods to initialize state. This lets us
        construct a :class:`Coverage` object, then tweak its state before this
        function is called.

        """
        if self._inited:
            return

        self._inited = True

        # Create and configure the debugging controller.
        self._debug = DebugControl(self.config.debug, self._debug_file, self.config.debug_file)
        if self._debug.should("process"):
            self._debug.write("Coverage._init")

        if "multiprocessing" in (self.config.concurrency or ()):
            # Multi-processing uses parallel for the subprocesses, so also use
            # it for the main process.
            self.config.parallel = True

        # _exclude_re is a dict that maps exclusion list names to compiled regexes.
        self._exclude_re = {}

        set_relative_directory()
        if self.config.relative_files:
            self._file_mapper = relative_filename

        # Load plugins
        self._plugins = Plugins(self._debug)
        if self._plugin_override:
            self._plugins.load_from_callables(self._plugin_override)
        else:
            self._plugins.load_from_config(self.config.plugins, self.config)

        # Run configuring plugins.
        for plugin in self._plugins.configurers:
            # We need an object with set_option and get_option. Either self or
            # self.config will do. Choosing randomly stops people from doing
            # other things with those objects, against the public API.  Yes,
            # this is a bit childish. :)
            plugin.configure([self, self.config][int(time.time()) % 2])

    def _post_init(self) -> None:
        """Stuff to do after everything is initialized."""
        if self._should_write_debug:
            self._should_write_debug = False
            self._write_startup_debug()

        # "[run] _crash" will raise an exception if the value is close by in
        # the call stack, for testing error handling.
        if self.config._crash and self.config._crash in short_stack():
            raise RuntimeError(f"Crashing because called by {self.config._crash}")

    def _write_startup_debug(self) -> None:
        """Write out debug info at startup if needed."""
        wrote_any = False
        with self._debug.without_callers():
            if self._debug.should("config"):
                config_info = self.config.debug_info()
                write_formatted_info(self._debug.write, "config", config_info)
                wrote_any = True

            if self._debug.should("sys"):
                write_formatted_info(self._debug.write, "sys", self.sys_info())
                for plugin in self._plugins:
                    header = "sys: " + plugin._coverage_plugin_name
                    info = plugin.sys_info()
                    write_formatted_info(self._debug.write, header, info)
                wrote_any = True

            if self._debug.should("pybehave"):
                write_formatted_info(self._debug.write, "pybehave", env.debug_info())
                wrote_any = True

        if wrote_any:
            write_formatted_info(self._debug.write, "end", ())

    def _should_trace(self, filename: str, frame: FrameType) -> TFileDisposition:
        """Decide whether to trace execution in `filename`.

        Calls `_should_trace_internal`, and returns the FileDisposition.

        """
        assert self._inorout is not None
        disp = self._inorout.should_trace(filename, frame)
        if self._debug.should("trace"):
            self._debug.write(disposition_debug_msg(disp))
        return disp

    def _check_include_omit_etc(self, filename: str, frame: FrameType) -> bool:
        """Check a file name against the include/omit/etc, rules, verbosely.

        Returns a boolean: True if the file should be traced, False if not.

        """
        assert self._inorout is not None
        reason = self._inorout.check_include_omit_etc(filename, frame)
        if self._debug.should("trace"):
            if not reason:
                msg = f"Including {filename!r}"
            else:
                msg = f"Not including {filename!r}: {reason}"
            self._debug.write(msg)

        return not reason

    def _warn(self, msg: str, slug: str | None = None, once: bool = False) -> None:
        """Use `msg` as a warning.

        For warning suppression, use `slug` as the shorthand.

        If `once` is true, only show this warning once (determined by the
        slug.)

        """
        if not self._no_warn_slugs:
            self._no_warn_slugs = set(self.config.disable_warnings)

        if slug in self._no_warn_slugs:
            # Don't issue the warning
            return

        self._warnings.append(msg)
        if slug:
            msg = f"{msg} ({slug})"
        if self._debug.should("pid"):
            msg = f"[{os.getpid()}] {msg}"
        warnings.warn(msg, category=CoverageWarning, stacklevel=2)

        if once:
            assert slug is not None
            self._no_warn_slugs.add(slug)

    def _message(self, msg: str) -> None:
        """Write a message to the user, if configured to do so."""
        if self._messages:
            print(msg)

    def get_option(self, option_name: str) -> TConfigValueOut | None:
        """Get an option from the configuration.

        `option_name` is a colon-separated string indicating the section and
        option name.  For example, the ``branch`` option in the ``[run]``
        section of the config file would be indicated with `"run:branch"`.

        Returns the value of the option.  The type depends on the option
        selected.

        As a special case, an `option_name` of ``"paths"`` will return an
        dictionary with the entire ``[paths]`` section value.

        .. versionadded:: 4.0

        """
        return self.config.get_option(option_name)

    def set_option(self, option_name: str, value: TConfigValueIn | TConfigSectionIn) -> None:
        """Set an option in the configuration.

        `option_name` is a colon-separated string indicating the section and
        option name.  For example, the ``branch`` option in the ``[run]``
        section of the config file would be indicated with ``"run:branch"``.

        `value` is the new value for the option.  This should be an
        appropriate Python value.  For example, use True for booleans, not the
        string ``"True"``.

        As an example, calling:

        .. code-block:: python

            cov.set_option("run:branch", True)

        has the same effect as this configuration file:

        .. code-block:: ini

            [run]
            branch = True

        As a special case, an `option_name` of ``"paths"`` will replace the
        entire ``[paths]`` section.  The value should be a dictionary.

        .. versionadded:: 4.0

        """
        self.config.set_option(option_name, value)

    def load(self) -> None:
        """Load previously-collected coverage data from the data file."""
        self._init()
        if self._collector is not None:
            self._collector.reset()
        should_skip = self.config.parallel and not os.path.exists(self.config.data_file)
        if not should_skip:
            self._init_data(suffix=None)
        self._post_init()
        if not should_skip:
            assert self._data is not None
            self._data.read()

    def _init_for_start(self) -> None:
        """Initialization for start()"""
        # Construct the collector.
        concurrency: list[str] = self.config.concurrency or []
        if "multiprocessing" in concurrency:
            if self.config.config_file is None:
                raise ConfigError("multiprocessing requires a configuration file")
            patch_multiprocessing(rcfile=self.config.config_file)

        dycon = self.config.dynamic_context
        if not dycon or dycon == "none":
            context_switchers = []
        elif dycon == "test_function":
            context_switchers = [should_start_context_test_function]
        else:
            raise ConfigError(f"Don't understand dynamic_context setting: {dycon!r}")

        context_switchers.extend(
            plugin.dynamic_context for plugin in self._plugins.context_switchers
        )

        should_start_context = combine_context_switchers(context_switchers)

        self._core = Core(
            warn=self._warn,
            config=self.config,
            dynamic_contexts=(should_start_context is not None),
            metacov=self._metacov,
        )
        self._collector = Collector(
            core=self._core,
            should_trace=self._should_trace,
            check_include=self._check_include_omit_etc,
            should_start_context=should_start_context,
            file_mapper=self._file_mapper,
            branch=self.config.branch,
            warn=self._warn,
            concurrency=concurrency,
        )

        suffix = self._data_suffix_specified
        if suffix:
            if not isinstance(suffix, str):
                # if data_suffix=True, use .machinename.pid.random
                suffix = True
        elif self.config.parallel:
            if suffix is None:
                suffix = True
            elif not isinstance(suffix, str):
                suffix = bool(suffix)
        else:
            suffix = None

        self._init_data(suffix)

        assert self._data is not None
        self._collector.use_data(self._data, self.config.context)

        # Early warning if we aren't going to be able to support plugins.
        if self._plugins.file_tracers and not self._core.supports_plugins:
            self._warn(
                "Plugin file tracers ({}) aren't supported with {}".format(
                    ", ".join(
                        plugin._coverage_plugin_name
                            for plugin in self._plugins.file_tracers
                    ),
                    self._collector.tracer_name(),
                ),
            )
            for plugin in self._plugins.file_tracers:
                plugin._coverage_enabled = False

        # Create the file classifying substructure.
        self._inorout = InOrOut(
            config=self.config,
            warn=self._warn,
            debug=(self._debug if self._debug.should("trace") else None),
            include_namespace_packages=self.config.include_namespace_packages,
        )
        self._inorout.plugins = self._plugins
        self._inorout.disp_class = self._core.file_disposition_class

        # It's useful to write debug info after initing for start.
        self._should_write_debug = True

        # Register our clean-up handlers.
        atexit.register(self._atexit)
        if self.config.sigterm:
            is_main = (threading.current_thread() == threading.main_thread())
            if is_main and not env.WINDOWS:
                # The Python docs seem to imply that SIGTERM works uniformly even
                # on Windows, but that's not my experience, and this agrees:
                # https://stackoverflow.com/questions/35772001/x/35792192#35792192
                self._old_sigterm = signal.signal(      # type: ignore[assignment]
                    signal.SIGTERM, self._on_sigterm,
                )

    def _init_data(self, suffix: str | bool | None) -> None:
        """Create a data file if we don't have one yet."""
        if self._data is None:
            # Create the data file.  We do this at construction time so that the
            # data file will be written into the directory where the process
            # started rather than wherever the process eventually chdir'd to.
            ensure_dir_for_file(self.config.data_file)
            self._data = CoverageData(
                basename=self.config.data_file,
                suffix=suffix,
                warn=self._warn,
                debug=self._debug,
                no_disk=self._no_disk,
            )

    def start(self) -> None:
        """Start measuring code coverage.

        Coverage measurement is only collected in functions called after
        :meth:`start` is invoked.  Statements in the same scope as
        :meth:`start` won't be measured.

        Once you invoke :meth:`start`, you must also call :meth:`stop`
        eventually, or your process might not shut down cleanly.

        The :meth:`collect` method is a context manager to handle both
        starting and stopping collection.

        """
        self._init()
        if not self._inited_for_start:
            self._inited_for_start = True
            self._init_for_start()
        self._post_init()

        assert self._collector is not None
        assert self._inorout is not None

        # Issue warnings for possible problems.
        self._inorout.warn_conflicting_settings()

        # See if we think some code that would eventually be measured has
        # already been imported.
        if self._warn_preimported_source:
            self._inorout.warn_already_imported_files()

        if self._auto_load:
            self.load()

        apply_patches(self, self.config, make_pth_file=self._make_pth_file)

        self._collector.start()
        self._started = True
        self._instances.append(self)

    def stop(self) -> None:
        """Stop measuring code coverage."""
        if self._instances:
            if self._instances[-1] is self:
                self._instances.pop()
        if self._started:
            assert self._collector is not None
            self._collector.stop()
        self._started = False

    @contextlib.contextmanager
    def collect(self) -> Iterator[None]:
        """A context manager to start/stop coverage measurement collection.

        .. versionadded:: 7.3

        """
        self.start()
        try:
            yield
        finally:
            self.stop()     # pragma: nested

    def _atexit(self, event: str = "atexit") -> None:
        """Clean up on process shutdown."""
        if self._debug.should("process"):
            self._debug.write(f"{event}: pid: {os.getpid()}, instance: {self!r}")
        if self._started:
            self.stop()
        if self._auto_save or event == "sigterm":
            self.save()

    def _on_sigterm(self, signum_unused: int, frame_unused: FrameType | None) -> None:
        """A handler for signal.SIGTERM."""
        self._atexit("sigterm")
        # Statements after here won't be seen by metacov because we just wrote
        # the data, and are about to kill the process.
        signal.signal(signal.SIGTERM, self._old_sigterm)    # pragma: not covered
        os.kill(os.getpid(), signal.SIGTERM)                # pragma: not covered

    def erase(self) -> None:
        """Erase previously collected coverage data.

        This removes the in-memory data collected in this session as well as
        discarding the data file.

        """
        self._init()
        self._post_init()
        if self._collector is not None:
            self._collector.reset()
        self._init_data(suffix=None)
        assert self._data is not None
        self._data.erase(parallel=self.config.parallel)
        self._data = None
        self._inited_for_start = False

    def switch_context(self, new_context: str) -> None:
        """Switch to a new dynamic context.

        `new_context` is a string to use as the :ref:`dynamic context
        <dynamic_contexts>` label for collected data.  If a :ref:`static
        context <static_contexts>` is in use, the static and dynamic context
        labels will be joined together with a pipe character.

        Coverage collection must be started already.

        .. versionadded:: 5.0

        """
        if not self._started:                           # pragma: part started
            raise CoverageException("Cannot switch context, coverage is not started")

        assert self._collector is not None
        if self._collector.should_start_context:
            self._warn("Conflicting dynamic contexts", slug="dynamic-conflict", once=True)

        self._collector.switch_context(new_context)

    def clear_exclude(self, which: str = "exclude") -> None:
        """Clear the exclude list."""
        self._init()
        setattr(self.config, which + "_list", [])
        self._exclude_regex_stale()

    def exclude(self, regex: str, which: str = "exclude") -> None:
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
        self._init()
        excl_list = getattr(self.config, which + "_list")
        excl_list.append(regex)
        self._exclude_regex_stale()

    def _exclude_regex_stale(self) -> None:
        """Drop all the compiled exclusion regexes, a list was modified."""
        self._exclude_re.clear()

    def _exclude_regex(self, which: str) -> str:
        """Return a regex string for the given exclusion list."""
        if which not in self._exclude_re:
            excl_list = getattr(self.config, which + "_list")
            self._exclude_re[which] = join_regex(excl_list)
        return self._exclude_re[which]

    def get_exclude_list(self, which: str = "exclude") -> list[str]:
        """Return a list of excluded regex strings.

        `which` indicates which list is desired.  See :meth:`exclude` for the
        lists that are available, and their meaning.

        """
        self._init()
        return cast(list[str], getattr(self.config, which + "_list"))

    def save(self) -> None:
        """Save the collected coverage data to the data file."""
        data = self.get_data()
        data.write()

    def _make_aliases(self) -> PathAliases:
        """Create a PathAliases from our configuration."""
        aliases = PathAliases(
            debugfn=(self._debug.write if self._debug.should("pathmap") else None),
            relative=self.config.relative_files,
        )
        for paths in self.config.paths.values():
            result = paths[0]
            for pattern in paths[1:]:
                aliases.add(pattern, result)
        return aliases

    def combine(
        self,
        data_paths: Iterable[str] | None = None,
        strict: bool = False,
        keep: bool = False,
    ) -> None:
        """Combine together a number of similarly-named coverage data files.

        All coverage data files whose name starts with `data_file` (from the
        coverage() constructor) will be read, and combined together into the
        current measurements.

        `data_paths` is a list of files or directories from which data should
        be combined. If no list is passed, then the data files from the
        directory indicated by the current data file (probably the current
        directory) will be combined.

        If `strict` is true, then it is an error to attempt to combine when
        there are no data files to combine.

        If `keep` is true, then original input data files won't be deleted.

        .. versionadded:: 4.0
            The `data_paths` parameter.

        .. versionadded:: 4.3
            The `strict` parameter.

        .. versionadded: 5.5
            The `keep` parameter.
        """
        self._init()
        self._init_data(suffix=None)
        self._post_init()
        self.get_data()

        assert self._data is not None
        combine_parallel_data(
            self._data,
            aliases=self._make_aliases(),
            data_paths=data_paths,
            strict=strict,
            keep=keep,
            message=self._message,
        )

    def get_data(self) -> CoverageData:
        """Get the collected data.

        Also warn about various problems collecting data.

        Returns a :class:`coverage.CoverageData`, the collected coverage data.

        .. versionadded:: 4.0

        """
        self._init()
        self._init_data(suffix=None)
        self._post_init()

        if self._collector is not None:
            for plugin in self._plugins:
                if not plugin._coverage_enabled:
                    self._collector.plugin_was_disabled(plugin)

            if self._collector.flush_data():
                self._post_save_work()

        assert self._data is not None
        return self._data

    def _post_save_work(self) -> None:
        """After saving data, look for warnings, post-work, etc.

        Warn about things that should have happened but didn't.
        Look for un-executed files.

        """
        assert self._data is not None
        assert self._inorout is not None

        # If there are still entries in the source_pkgs_unmatched list,
        # then we never encountered those packages.
        if self._warn_unimported_source:
            self._inorout.warn_unimported_source()

        # Find out if we got any data.
        if not self._data and self._warn_no_data:
            self._warn("No data was collected.", slug="no-data-collected")

        # Touch all the files that could have executed, so that we can
        # mark completely un-executed files as 0% covered.
        file_paths = collections.defaultdict(list)
        for file_path, plugin_name in self._inorout.find_possibly_unexecuted_files():
            file_path = self._file_mapper(file_path)
            file_paths[plugin_name].append(file_path)
        for plugin_name, paths in file_paths.items():
            self._data.touch_files(paths, plugin_name)

    # Backward compatibility with version 1.
    def analysis(self, morf: TMorf) -> tuple[str, list[TLineNo], list[TLineNo], str]:
        """Like `analysis2` but doesn't return excluded line numbers."""
        f, s, _, m, mf = self.analysis2(morf)
        return f, s, m, mf

    def analysis2(
        self,
        morf: TMorf,
    ) -> tuple[str, list[TLineNo], list[TLineNo], list[TLineNo], str]:
        """Analyze a module.

        `morf` is a module or a file name.  It will be analyzed to determine
        its coverage statistics.  The return value is a 5-tuple:

        * The file name for the module.
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

    @functools.lru_cache(maxsize=1)
    def _analyze(self, morf: TMorf) -> Analysis:
        """Analyze a module or file.  Private for now."""
        self._init()
        self._post_init()

        data = self.get_data()
        file_reporter = self._get_file_reporter(morf)
        filename = self._file_mapper(file_reporter.filename)
        return analysis_from_file_reporter(data, self.config.precision, file_reporter, filename)

    def branch_stats(self, morf: TMorf) -> dict[TLineNo, tuple[int, int]]:
        """Get branch statistics about a module.

        `morf` is a module or a file name.

        Returns a dict mapping line numbers to a tuple:
        (total_exits, taken_exits).

        .. versionadded:: 7.7

        """
        analysis = self._analyze(morf)
        return analysis.branch_stats()

    @functools.lru_cache(maxsize=1)
    def _get_file_reporter(self, morf: TMorf) -> FileReporter:
        """Get a FileReporter for a module or file name."""
        assert self._data is not None
        plugin = None
        file_reporter: str | FileReporter = "python"

        if isinstance(morf, str):
            mapped_morf = self._file_mapper(morf)
            plugin_name = self._data.file_tracer(mapped_morf)
            if plugin_name:
                plugin = self._plugins.get(plugin_name)

                if plugin:
                    file_reporter = plugin.file_reporter(mapped_morf)
                    if file_reporter is None:
                        raise PluginError(
                            "Plugin {!r} did not provide a file reporter for {!r}.".format(
                                plugin._coverage_plugin_name, morf,
                            ),
                        )

        if file_reporter == "python":
            file_reporter = PythonFileReporter(morf, self)

        assert isinstance(file_reporter, FileReporter)
        return file_reporter

    def _get_file_reporters(
        self,
        morfs: Iterable[TMorf] | None = None,
    ) -> list[tuple[FileReporter, TMorf]]:
        """Get FileReporters for a list of modules or file names.

        For each module or file name in `morfs`, find a FileReporter.  Return
        a list pairing FileReporters with the morfs.

        If `morfs` is a single module or file name, this returns a list of one
        FileReporter.  If `morfs` is empty or None, then the list of all files
        measured is used to find the FileReporters.

        """
        assert self._data is not None
        if not morfs:
            morfs = self._data.measured_files()

        # Be sure we have a collection.
        if not isinstance(morfs, (list, tuple, set)):
            morfs = [morfs]     # type: ignore[list-item]

        return [(self._get_file_reporter(morf), morf) for morf in morfs]

    def _prepare_data_for_reporting(self) -> None:
        """Re-map data before reporting, to get implicit "combine" behavior."""
        if self.config.paths:
            mapped_data = CoverageData(warn=self._warn, debug=self._debug, no_disk=True)
            if self._data is not None:
                mapped_data.update(self._data, map_path=self._make_aliases().map)
            self._data = mapped_data

    def report(
        self,
        morfs: Iterable[TMorf] | None = None,
        show_missing: bool | None = None,
        ignore_errors: bool | None = None,
        file: IO[str] | None = None,
        omit: str | list[str] | None = None,
        include: str | list[str] | None = None,
        skip_covered: bool | None = None,
        contexts: list[str] | None = None,
        skip_empty: bool | None = None,
        precision: int | None = None,
        sort: str | None = None,
        output_format: str | None = None,
    ) -> float:
        """Write a textual summary report to `file`.

        Each module in `morfs` is listed, with counts of statements, executed
        statements, missing statements, and a list of lines missed.

        If `show_missing` is true, then details of which lines or branches are
        missing will be included in the report.  If `ignore_errors` is true,
        then a failure while reporting a single file will not stop the entire
        report.

        `file` is a file-like object, suitable for writing.

        `output_format` determines the format, either "text" (the default),
        "markdown", or "total".

        `include` is a list of file name patterns.  Files that match will be
        included in the report. Files matching `omit` will not be included in
        the report.

        If `skip_covered` is true, don't report on files with 100% coverage.

        If `skip_empty` is true, don't report on empty files (those that have
        no statements).

        `contexts` is a list of regular expression strings.  Only data from
        :ref:`dynamic contexts <dynamic_contexts>` that match one of those
        expressions (using :func:`re.search <python:re.search>`) will be
        included in the report.

        `precision` is the number of digits to display after the decimal
        point for percentages.

        All of the arguments default to the settings read from the
        :ref:`configuration file <config>`.

        Returns a float, the total percentage covered.

        .. versionadded:: 4.0
            The `skip_covered` parameter.

        .. versionadded:: 5.0
            The `contexts` and `skip_empty` parameters.

        .. versionadded:: 5.2
            The `precision` parameter.

        .. versionadded:: 7.0
            The `format` parameter.

        """
        self._prepare_data_for_reporting()
        with override_config(
            self,
            ignore_errors=ignore_errors,
            report_omit=omit,
            report_include=include,
            show_missing=show_missing,
            skip_covered=skip_covered,
            report_contexts=contexts,
            skip_empty=skip_empty,
            precision=precision,
            sort=sort,
            format=output_format,
        ):
            reporter = SummaryReporter(self)
            return reporter.report(morfs, outfile=file)

    def annotate(
        self,
        morfs: Iterable[TMorf] | None = None,
        directory: str | None = None,
        ignore_errors: bool | None = None,
        omit: str | list[str] | None = None,
        include: str | list[str] | None = None,
        contexts: list[str] | None = None,
    ) -> None:
        """Annotate a list of modules.

        Each module in `morfs` is annotated.  The source is written to a new
        file, named with a ",cover" suffix, with each line prefixed with a
        marker to indicate the coverage of the line.  Covered lines have ">",
        excluded lines have "-", and missing lines have "!".

        See :meth:`report` for other arguments.

        """
        self._prepare_data_for_reporting()
        with override_config(
            self,
            ignore_errors=ignore_errors,
            report_omit=omit,
            report_include=include,
            report_contexts=contexts,
        ):
            reporter = AnnotateReporter(self)
            reporter.report(morfs, directory=directory)

    def html_report(
        self,
        morfs: Iterable[TMorf] | None = None,
        directory: str | None = None,
        ignore_errors: bool | None = None,
        omit: str | list[str] | None = None,
        include: str | list[str] | None = None,
        extra_css: str | None = None,
        title: str | None = None,
        skip_covered: bool | None = None,
        show_contexts: bool | None = None,
        contexts: list[str] | None = None,
        skip_empty: bool | None = None,
        precision: int | None = None,
    ) -> float:
        """Generate an HTML report.

        The HTML is written to `directory`.  The file "index.html" is the
        overview starting point, with links to more detailed pages for
        individual modules.

        `extra_css` is a path to a file of other CSS to apply on the page.
        It will be copied into the HTML directory.

        `title` is a text string (not HTML) to use as the title of the HTML
        report.

        See :meth:`report` for other arguments.

        Returns a float, the total percentage covered.

        .. note::

            The HTML report files are generated incrementally based on the
            source files and coverage results. If you modify the report files,
            the changes will not be considered.  You should be careful about
            changing the files in the report folder.

        """
        self._prepare_data_for_reporting()
        with override_config(
            self,
            ignore_errors=ignore_errors,
            report_omit=omit,
            report_include=include,
            html_dir=directory,
            extra_css=extra_css,
            html_title=title,
            html_skip_covered=skip_covered,
            show_contexts=show_contexts,
            report_contexts=contexts,
            html_skip_empty=skip_empty,
            precision=precision,
        ):
            reporter = HtmlReporter(self)
            ret = reporter.report(morfs)
            return ret

    def xml_report(
        self,
        morfs: Iterable[TMorf] | None = None,
        outfile: str | None = None,
        ignore_errors: bool | None = None,
        omit: str | list[str] | None = None,
        include: str | list[str] | None = None,
        contexts: list[str] | None = None,
        skip_empty: bool | None = None,
    ) -> float:
        """Generate an XML report of coverage results.

        The report is compatible with Cobertura reports.

        Each module in `morfs` is included in the report.  `outfile` is the
        path to write the file to, "-" will write to stdout.

        See :meth:`report` for other arguments.

        Returns a float, the total percentage covered.

        """
        self._prepare_data_for_reporting()
        with override_config(
            self,
            ignore_errors=ignore_errors,
            report_omit=omit,
            report_include=include,
            xml_output=outfile,
            report_contexts=contexts,
            skip_empty=skip_empty,
        ):
            return render_report(self.config.xml_output, XmlReporter(self), morfs, self._message)

    def json_report(
        self,
        morfs: Iterable[TMorf] | None = None,
        outfile: str | None = None,
        ignore_errors: bool | None = None,
        omit: str | list[str] | None = None,
        include: str | list[str] | None = None,
        contexts: list[str] | None = None,
        pretty_print: bool | None = None,
        show_contexts: bool | None = None,
    ) -> float:
        """Generate a JSON report of coverage results.

        Each module in `morfs` is included in the report.  `outfile` is the
        path to write the file to, "-" will write to stdout.

        `pretty_print` is a boolean, whether to pretty-print the JSON output or not.

        See :meth:`report` for other arguments.

        Returns a float, the total percentage covered.

        .. versionadded:: 5.0

        """
        self._prepare_data_for_reporting()
        with override_config(
            self,
            ignore_errors=ignore_errors,
            report_omit=omit,
            report_include=include,
            json_output=outfile,
            report_contexts=contexts,
            json_pretty_print=pretty_print,
            json_show_contexts=show_contexts,
        ):
            return render_report(self.config.json_output, JsonReporter(self), morfs, self._message)

    def lcov_report(
        self,
        morfs: Iterable[TMorf] | None = None,
        outfile: str | None = None,
        ignore_errors: bool | None = None,
        omit: str | list[str] | None = None,
        include: str | list[str] | None = None,
        contexts: list[str] | None = None,
    ) -> float:
        """Generate an LCOV report of coverage results.

        Each module in `morfs` is included in the report. `outfile` is the
        path to write the file to, "-" will write to stdout.

        See :meth:`report` for other arguments.

        .. versionadded:: 6.3
        """
        self._prepare_data_for_reporting()
        with override_config(
            self,
            ignore_errors=ignore_errors,
            report_omit=omit,
            report_include=include,
            lcov_output=outfile,
            report_contexts=contexts,
        ):
            return render_report(self.config.lcov_output, LcovReporter(self), morfs, self._message)

    def sys_info(self) -> Iterable[tuple[str, Any]]:
        """Return a list of (key, value) pairs showing internal information."""

        import coverage as covmod

        self._init()
        self._post_init()

        def plugin_info(plugins: list[Any]) -> list[str]:
            """Make an entry for the sys_info from a list of plug-ins."""
            entries = []
            for plugin in plugins:
                entry = plugin._coverage_plugin_name
                if not plugin._coverage_enabled:
                    entry += " (disabled)"
                entries.append(entry)
            return entries

        info = [
            ("coverage_version", covmod.__version__),
            ("coverage_module", covmod.__file__),
            ("core", self._collector.tracer_name() if self._collector is not None else "-none-"),
            ("CTracer", f"available from {CTRACER_FILE}" if CTRACER_FILE else "unavailable"),
            ("plugins.file_tracers", plugin_info(self._plugins.file_tracers)),
            ("plugins.configurers", plugin_info(self._plugins.configurers)),
            ("plugins.context_switchers", plugin_info(self._plugins.context_switchers)),
            ("configs_attempted", self.config.config_files_attempted),
            ("configs_read", self.config.config_files_read),
            ("config_file", self.config.config_file),
            ("config_contents",
                repr(self.config._config_contents) if self.config._config_contents else "-none-",
            ),
            ("data_file", self._data.data_filename() if self._data is not None else "-none-"),
            ("python", sys.version.replace("\n", "")),
            ("platform", platform.platform()),
            ("implementation", platform.python_implementation()),
            ("build", platform.python_build()),
            ("gil_enabled", getattr(sys, '_is_gil_enabled', lambda: True)()),
            ("executable", sys.executable),
            ("def_encoding", sys.getdefaultencoding()),
            ("fs_encoding", sys.getfilesystemencoding()),
            ("pid", os.getpid()),
            ("cwd", os.getcwd()),
            ("path", sys.path),
            ("environment", [f"{k} = {v}" for k, v in relevant_environment_display(os.environ)]),
            ("command_line", " ".join(getattr(sys, "argv", ["-none-"]))),
        ]

        if self._inorout is not None:
            info.extend(self._inorout.sys_info())

        info.extend(CoverageData.sys_info())

        return info


# Mega debugging...
# $set_env.py: COVERAGE_DEBUG_CALLS - Lots and lots of output about calls to Coverage.
if int(os.getenv("COVERAGE_DEBUG_CALLS", 0)):               # pragma: debugging
    from coverage.debug import decorate_methods, show_calls

    Coverage = decorate_methods(        # type: ignore[misc]
        show_calls(show_args=True),
        butnot=["get_data"],
    )(Coverage)


def process_startup() -> Coverage | None:
    """Call this at Python start-up to perhaps measure coverage.

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

    Returns the :class:`Coverage` instance that was started, or None if it was
    not started by this call.

    """
    cps = os.getenv("COVERAGE_PROCESS_START")
    if not cps:
        # No request for coverage, nothing to do.
        return None

    # This function can be called more than once in a process. This happens
    # because some virtualenv configurations make the same directory visible
    # twice in sys.path.  This means that the .pth file will be found twice,
    # and executed twice, executing this function twice.  We set a global
    # flag (an attribute on this function) to indicate that coverage.py has
    # already been started, so we can avoid doing it twice.
    #
    # https://github.com/nedbat/coveragepy/issues/340 has more details.

    if hasattr(process_startup, "coverage"):
        # We've annotated this function before, so we must have already
        # started coverage.py in this process.  Nothing to do.
        return None

    cov = Coverage(config_file=cps)
    process_startup.coverage = cov      # type: ignore[attr-defined]
    cov._warn_no_data = False
    cov._warn_unimported_source = False
    cov._warn_preimported_source = False
    cov._auto_save = True
    cov._make_pth_file = False
    cov.start()

    return cov


def _prevent_sub_process_measurement() -> None:
    """Stop any subprocess auto-measurement from writing data."""
    auto_created_coverage = getattr(process_startup, "coverage", None)
    if auto_created_coverage is not None:
        auto_created_coverage._auto_save = False
