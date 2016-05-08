# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

"""Base test case class for coverage.py testing."""

import contextlib
import datetime
import glob
import os
import random
import re
import shlex
import shutil
import sys

import coverage
from coverage.backunittest import TestCase
from coverage.backward import StringIO, import_local_file, string_class, shlex_quote
from coverage.cmdline import CoverageScript
from coverage.debug import _TEST_NAME_FILE, DebugControl
from coverage.test_helpers import (
    EnvironmentAwareMixin, StdStreamCapturingMixin, TempDirMixin,
    DelayedAssertionMixin,
)

from nose.plugins.skip import SkipTest

from tests.helpers import run_command


# Status returns for the command line.
OK, ERR = 0, 1


class CoverageTest(
    EnvironmentAwareMixin,
    StdStreamCapturingMixin,
    TempDirMixin,
    DelayedAssertionMixin,
    TestCase
):
    """A base class for coverage.py test cases."""

    # Standard unittest setting: show me diffs even if they are very long.
    maxDiff = None

    # Tell newer unittest implementations to print long helpful messages.
    longMessage = True

    def setUp(self):
        super(CoverageTest, self).setUp()

        # Attributes for getting info about what happened.
        self.last_command_status = None
        self.last_command_output = None
        self.last_module_name = None

        if _TEST_NAME_FILE:                                 # pragma: debugging
            with open(_TEST_NAME_FILE, "w") as f:
                f.write("%s_%s" % (
                    self.__class__.__name__, self._testMethodName,
                ))

    def skip(self, reason):
        """Skip this test, and give a reason."""
        self.class_behavior().skipped += 1
        raise SkipTest(reason)

    def clean_local_file_imports(self):
        """Clean up the results of calls to `import_local_file`.

        Use this if you need to `import_local_file` the same file twice in
        one test.

        """
        # So that we can re-import files, clean them out first.
        self.cleanup_modules()
        # Also have to clean out the .pyc file, since the timestamp
        # resolution is only one second, a changed file might not be
        # picked up.
        for pyc in glob.glob('*.pyc'):
            os.remove(pyc)
        if os.path.exists("__pycache__"):
            shutil.rmtree("__pycache__")

    def import_local_file(self, modname, modfile=None):
        """Import a local file as a module.

        Opens a file in the current directory named `modname`.py, imports it
        as `modname`, and returns the module object. `modfile` is the file to
        import if it isn't in the current directory.

        """
        return import_local_file(modname, modfile)

    def start_import_stop(self, cov, modname, modfile=None):
        """Start coverage, import a file, then stop coverage.

        `cov` is started and stopped, with an `import_local_file` of
        `modname` in the middle. `modfile` is the file to import as `modname`
        if it isn't in the current directory.

        The imported module is returned.

        """
        cov.start()
        try:                                    # pragma: nested
            # Import the Python file, executing it.
            mod = self.import_local_file(modname, modfile)
        finally:                                # pragma: nested
            # Stop coverage.py.
            cov.stop()
        return mod

    def get_module_name(self):
        """Return a random module name to use for this test run."""
        self.last_module_name = 'coverage_test_' + str(random.random())[2:]
        return self.last_module_name

    # Map chars to numbers for arcz_to_arcs
    _arcz_map = {'.': -1}
    _arcz_map.update(dict((c, ord(c) - ord('0')) for c in '123456789'))
    _arcz_map.update(dict(
        (c, 10 + ord(c) - ord('A')) for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    ))

    def arcz_to_arcs(self, arcz):
        """Convert a compact textual representation of arcs to a list of pairs.

        The text has space-separated pairs of letters.  Period is -1, 1-9 are
        1-9, A-Z are 10 through 36.  The resulting list is sorted regardless of
        the order of the input pairs.

        ".1 12 2." --> [(-1,1), (1,2), (2,-1)]

        Minus signs can be included in the pairs:

        "-11, 12, 2-5" --> [(-1,1), (1,2), (2,-5)]

        """
        arcs = []
        for pair in arcz.split():
            asgn = bsgn = 1
            if len(pair) == 2:
                a, b = pair
            else:
                assert len(pair) == 3
                if pair[0] == '-':
                    _, a, b = pair
                    asgn = -1
                else:
                    assert pair[1] == '-'
                    a, _, b = pair
                    bsgn = -1
            arcs.append((asgn * self._arcz_map[a], bsgn * self._arcz_map[b]))
        return sorted(arcs)

    def assert_equal_args(self, a1, a2, msg=None):
        """Assert that the arc lists `a1` and `a2` are equal."""
        # Make them into multi-line strings so we can see what's going wrong.
        s1 = "\n".join(repr(a) for a in a1) + "\n"
        s2 = "\n".join(repr(a) for a in a2) + "\n"
        self.assertMultiLineEqual(s1, s2, msg)

    def check_coverage(
        self, text, lines=None, missing="", report="",
        excludes=None, partials="",
        arcz=None, arcz_missing="", arcz_unpredicted="",
        arcs=None, arcs_missing=None, arcs_unpredicted=None,
    ):
        """Check the coverage measurement of `text`.

        The source `text` is run and measured.  `lines` are the line numbers
        that are executable, or a list of possible line numbers, any of which
        could match. `missing` are the lines not executed, `excludes` are
        regexes to match against for excluding lines, and `report` is the text
        of the measurement report.

        For arc measurement, `arcz` is a string that can be decoded into arcs
        in the code (see `arcz_to_arcs` for the encoding scheme).
        `arcz_missing` are the arcs that are not executed, and
        `arcz_unpredicted` are the arcs executed in the code, but not deducible
        from the code.  These last two default to "", meaning we explicitly
        check that there are no missing or unpredicted arcs.

        Returns the Coverage object, in case you want to poke at it some more.

        """
        # We write the code into a file so that we can import it.
        # Coverage.py wants to deal with things as modules with file names.
        modname = self.get_module_name()

        self.make_file(modname + ".py", text)

        if arcs is None and arcz is not None:
            arcs = self.arcz_to_arcs(arcz)
        if arcs_missing is None:
            arcs_missing = self.arcz_to_arcs(arcz_missing)
        if arcs_unpredicted is None:
            arcs_unpredicted = self.arcz_to_arcs(arcz_unpredicted)

        # Start up coverage.py.
        cov = coverage.Coverage(branch=True)
        cov.erase()
        for exc in excludes or []:
            cov.exclude(exc)
        for par in partials or []:
            cov.exclude(par, which='partial')

        mod = self.start_import_stop(cov, modname)

        # Clean up our side effects
        del sys.modules[modname]

        # Get the analysis results, and check that they are right.
        analysis = cov._analyze(mod)
        statements = sorted(analysis.statements)
        if lines is not None:
            if isinstance(lines[0], int):
                # lines is just a list of numbers, it must match the statements
                # found in the code.
                self.assertEqual(statements, lines)
            else:
                # lines is a list of possible line number lists, one of them
                # must match.
                for line_list in lines:
                    if statements == line_list:
                        break
                else:
                    self.fail("None of the lines choices matched %r" % statements)

            missing_formatted = analysis.missing_formatted()
            if isinstance(missing, string_class):
                self.assertEqual(missing_formatted, missing)
            else:
                for missing_list in missing:
                    if missing_formatted == missing_list:
                        break
                else:
                    self.fail("None of the missing choices matched %r" % missing_formatted)

        if arcs is not None:
            with self.delayed_assertions():
                self.assert_equal_args(
                    analysis.arc_possibilities(), arcs,
                    "Possible arcs differ",
                )

                self.assert_equal_args(
                    analysis.arcs_missing(), arcs_missing,
                    "Missing arcs differ"
                )

                self.assert_equal_args(
                    analysis.arcs_unpredicted(), arcs_unpredicted,
                    "Unpredicted arcs differ"
                )

        if report:
            frep = StringIO()
            cov.report(mod, file=frep, show_missing=True)
            rep = " ".join(frep.getvalue().split("\n")[2].split()[1:])
            self.assertEqual(report, rep)

        return cov

    @contextlib.contextmanager
    def assert_warnings(self, cov, warnings):
        """A context manager to check that particular warnings happened in `cov`."""
        saved_warnings = []
        def capture_warning(msg):
            """A fake implementation of Coverage._warn, to capture warnings."""
            saved_warnings.append(msg)

        original_warn = cov._warn
        cov._warn = capture_warning

        try:
            yield
        except:
            raise
        else:
            for warning_regex in warnings:
                for saved in saved_warnings:
                    if re.search(warning_regex, saved):
                        break
                else:
                    self.fail("Didn't find warning %r in %r" % (warning_regex, saved_warnings))
            cov._warn = original_warn

    def nice_file(self, *fparts):
        """Canonicalize the file name composed of the parts in `fparts`."""
        fname = os.path.join(*fparts)
        return os.path.normcase(os.path.abspath(os.path.realpath(fname)))

    def assert_same_files(self, flist1, flist2):
        """Assert that `flist1` and `flist2` are the same set of file names."""
        flist1_nice = [self.nice_file(f) for f in flist1]
        flist2_nice = [self.nice_file(f) for f in flist2]
        self.assertCountEqual(flist1_nice, flist2_nice)

    def assert_exists(self, fname):
        """Assert that `fname` is a file that exists."""
        msg = "File %r should exist" % fname
        self.assertTrue(os.path.exists(fname), msg)

    def assert_doesnt_exist(self, fname):
        """Assert that `fname` is a file that doesn't exist."""
        msg = "File %r shouldn't exist" % fname
        self.assertTrue(not os.path.exists(fname), msg)

    def assert_starts_with(self, s, prefix, msg=None):
        """Assert that `s` starts with `prefix`."""
        if not s.startswith(prefix):
            self.fail(msg or ("%r doesn't start with %r" % (s, prefix)))

    def assert_recent_datetime(self, dt, seconds=10, msg=None):
        """Assert that `dt` marks a time at most `seconds` seconds ago."""
        age = datetime.datetime.now() - dt
        # Python2.6 doesn't have total_seconds :(
        self.assertEqual(age.days, 0, msg)
        self.assertGreaterEqual(age.seconds, 0, msg)
        self.assertLessEqual(age.seconds, seconds, msg)

    def command_line(self, args, ret=OK, _covpkg=None):
        """Run `args` through the command line.

        Use this when you want to run the full coverage machinery, but in the
        current process.  Exceptions may be thrown from deep in the code.
        Asserts that `ret` is returned by `CoverageScript.command_line`.

        Compare with `run_command`.

        Returns None.

        """
        script = CoverageScript(_covpkg=_covpkg)
        ret_actual = script.command_line(shlex.split(args))
        self.assertEqual(ret_actual, ret)

    coverage_command = "coverage"

    def run_command(self, cmd):
        """Run the command-line `cmd` in a sub-process.

        `cmd` is the command line to invoke in a sub-process. Returns the
        combined content of `stdout` and `stderr` output streams from the
        sub-process.

        Use this when you need to test the process behavior of coverage.

        Compare with `command_line`.

        Handles the following command name specially:

        * "python" is replaced with the command name of the current
            Python interpreter.

        * "coverage" is replaced with the command name for the main
            Coverage.py program.

        """
        split_commandline = cmd.split(" ", 1)
        command_name = split_commandline[0]
        command_args = split_commandline[1:]

        if command_name == "python":
            # Running a Python interpreter in a sub-processes can be tricky.
            # Use the real name of our own executable. So "python foo.py" might
            # get executed as "python3.3 foo.py". This is important because
            # Python 3.x doesn't install as "python", so you might get a Python
            # 2 executable instead if you don't use the executable's basename.
            command_name = os.path.basename(sys.executable)

        if command_name == "coverage":
            # The invocation requests the Coverage.py program.  Substitute the
            # actual Coverage.py main command name.
            command_name = self.coverage_command

        full_commandline = " ".join([shlex_quote(command_name)] + command_args)

        _, output = self.run_command_status(full_commandline)
        return output

    def run_command_status(self, cmd):
        """Run the command-line `cmd` in a sub-process, and print its output.

        Use this when you need to test the process behavior of coverage.

        Compare with `command_line`.

        Returns a pair: the process' exit status and stdout text, which are
        also stored as self.last_command_status and self.last_command_output.

        """
        # Add our test modules directory to PYTHONPATH.  I'm sure there's too
        # much path munging here, but...
        here = os.path.dirname(self.nice_file(coverage.__file__, ".."))
        testmods = self.nice_file(here, 'tests/modules')
        zipfile = self.nice_file(here, 'tests/zipmods.zip')
        pypath = os.getenv('PYTHONPATH', '')
        if pypath:
            pypath += os.pathsep
        pypath += testmods + os.pathsep + zipfile
        self.set_environ('PYTHONPATH', pypath)

        self.last_command_status, self.last_command_output = run_command(cmd)
        print(self.last_command_output)
        return self.last_command_status, self.last_command_output

    def report_from_command(self, cmd):
        """Return the report from the `cmd`, with some convenience added."""
        report = self.run_command(cmd).replace('\\', '/')
        self.assertNotIn("error", report.lower())
        return report

    def report_lines(self, report):
        """Return the lines of the report, as a list."""
        lines = report.split('\n')
        self.assertEqual(lines[-1], "")
        return lines[:-1]

    def line_count(self, report):
        """How many lines are in `report`?"""
        return len(self.report_lines(report))

    def squeezed_lines(self, report):
        """Return a list of the lines in report, with the spaces squeezed."""
        lines = self.report_lines(report)
        return [re.sub(r"\s+", " ", l.strip()) for l in lines]

    def last_line_squeezed(self, report):
        """Return the last line of `report` with the spaces squeezed down."""
        return self.squeezed_lines(report)[-1]


class DebugControlString(DebugControl):
    """A `DebugControl` that writes to a StringIO, for testing."""
    def __init__(self, options):
        super(DebugControlString, self).__init__(options, StringIO())

    def get_output(self):
        """Get the output text from the `DebugControl`."""
        return self.output.getvalue()
