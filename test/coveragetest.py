"""Base test case class for coverage testing."""

import imp, os, random, shlex, shutil, sys, tempfile, textwrap

import coverage
from coverage.backward import sorted, StringIO      # pylint: disable-msg=W0622
from backtest import run_command
from backunittest import TestCase

class Tee(object):
    """A file-like that writes to all the file-likes it has."""

    def __init__(self, *files):
        """Make a Tee that writes to all the files in `files.`"""
        self.files = files

    def write(self, data):
        """Write `data` to all the files."""
        for f in self.files:
            f.write(data)


# Status returns for the command line.
OK, ERR = 0, 1

class CoverageTest(TestCase):
    """A base class for Coverage test cases."""

    run_in_temp_dir = True

    def setUp(self):
        if self.run_in_temp_dir:
            # Create a temporary directory.
            self.noise = str(random.random())[2:]
            self.temp_root = os.path.join(tempfile.gettempdir(), 'test_cover')
            self.temp_dir = os.path.join(self.temp_root, self.noise)
            os.makedirs(self.temp_dir)
            self.old_dir = os.getcwd()
            os.chdir(self.temp_dir)


            # Modules should be importable from this temp directory.
            self.old_syspath = sys.path[:]
            sys.path.insert(0, '')

            # Keep a counter to make every call to check_coverage unique.
            self.n = 0

        # Record environment variables that we changed with set_environ.
        self.environ_undos = {}

        # Use a Tee to capture stdout.
        self.old_stdout = sys.stdout
        self.captured_stdout = StringIO()
        sys.stdout = Tee(sys.stdout, self.captured_stdout)

    def tearDown(self):
        if self.run_in_temp_dir:
            # Restore the original sys.path.
            sys.path = self.old_syspath

            # Get rid of the temporary directory.
            os.chdir(self.old_dir)
            shutil.rmtree(self.temp_root)

        # Restore the environment.
        self.undo_environ()

        # Restore stdout.
        sys.stdout = self.old_stdout

    def set_environ(self, name, value):
        """Set an environment variable `name` to be `value`.

        The environment variable is set, and record is kept that it was set,
        so that `tearDown` can restore its original value.

        """
        if name not in self.environ_undos:
            self.environ_undos[name] = os.environ.get(name)
        os.environ[name] = value

    def original_environ(self, name):
        """The environment variable `name` from when the test started."""
        if name in self.environ_undos:
            return self.environ_undos[name]
        else:
            return os.environ[name]

    def undo_environ(self):
        """Undo all the changes made by `set_environ`."""
        for name, value in self.environ_undos.items():
            if value is None:
                del os.environ[name]
            else:
                os.environ[name] = value

    def stdout(self):
        """Return the data written to stdout during the test."""
        return self.captured_stdout.getvalue()

    def make_file(self, filename, text):
        """Create a temp file.

        `filename` is the file name, and `text` is the content.

        """
        # Tests that call `make_file` should be run in a temp environment.
        assert self.run_in_temp_dir
        text = textwrap.dedent(text)

        # Create the file.
        f = open(filename, 'w')
        f.write(text)
        f.close()

    def import_module(self, modname):
        """Import the module named modname, and return the module object."""
        modfile = modname + '.py'
        f = open(modfile, 'r')

        for suff in imp.get_suffixes():
            if suff[0] == '.py':
                break
        try:
            # pylint: disable-msg=W0631
            # (Using possibly undefined loop variable 'suff')
            mod = imp.load_module(modname, f, modfile, suff)
        finally:
            f.close()
        return mod

    def get_module_name(self):
        """Return the module name to use for this test run."""
        # We append self.n because otherwise two calls in one test will use the
        # same filename and whether the test works or not depends on the
        # timestamps in the .pyc file, so it becomes random whether the second
        # call will use the compiled version of the first call's code or not!
        modname = 'coverage_test_' + self.noise + str(self.n)
        self.n += 1
        return modname

    # Map chars to numbers for arcz_to_arcs
    _arcz_map = {'.': -1}
    _arcz_map.update(dict([(c, ord(c)-ord('0')) for c in '123456789']))
    _arcz_map.update(dict(
        [(c, 10+ord(c)-ord('A')) for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ']
        ))

    def arcz_to_arcs(self, arcz):
        """Convert a compact textual representation of arcs to a list of pairs.

        The text has space-separated pairs of letters.  Period is -1, 1-9 are
        1-9, A-Z are 10 through 36.  The resulting list is sorted regardless of
        the order of the input pairs.

        ".1 12 2." --> [(-1,1), (1,2), (2,-1)]

        """
        arcs = []
        for a,b in arcz.split():
            arcs.append((self._arcz_map[a], self._arcz_map[b]))
        return sorted(arcs)

    def assertEqualArcs(self, a1, a2):
        """Assert that the arc lists `a1` and `a2` are equal."""
        # Make them into multi-line strings so we can see what's going wrong.
        s1 = "\n".join([repr(a) for a in a1]) + "\n"
        s2 = "\n".join([repr(a) for a in a2]) + "\n"
        self.assertMultiLineEqual(s1, s2)

    def check_coverage(self, text, lines=None, missing="", excludes=None,
            report="", arcz=None, arcz_missing="", arcz_unpredicted=""):
        """Check the coverage measurement of `text`.

        The source `text` is run and measured.  `lines` are the line numbers
        that are executable, or a list of possible line numbers, any of which
        could match. `missing` are the lines not executed, `excludes` are
        regexes to match against for excluding lines, and `report` is the text
        of the measurement report.

        For arc measurement, `arcz` is a string that can be decoded into arcs
        in the code (see `arcz_to_arcs` for the encoding scheme),
        `arcz_missing` are the arcs that are not executed, and
        `arcs_unpredicted` are the arcs executed in the code, but not deducible
        from the code.

        """
        # We write the code into a file so that we can import it.
        # Coverage wants to deal with things as modules with file names.
        modname = self.get_module_name()

        self.make_file(modname+".py", text)

        arcs = arcs_missing = arcs_unpredicted = None
        if arcz is not None:
            arcs = self.arcz_to_arcs(arcz)
            arcs_missing = self.arcz_to_arcs(arcz_missing or "")
            arcs_unpredicted = self.arcz_to_arcs(arcz_unpredicted or "")

        # Start up Coverage.
        cov = coverage.coverage(branch=(arcs_missing is not None))
        cov.erase()
        for exc in excludes or []:
            cov.exclude(exc)
        cov.start()

        try:
            # Import the python file, executing it.
            mod = self.import_module(modname)
        finally:
            # Stop Coverage.
            cov.stop()

        # Clean up our side effects
        del sys.modules[modname]

        # Get the analysis results, and check that they are right.
        analysis = cov._analyze(mod)
        if lines is not None:
            if type(lines[0]) == type(1):
                # lines is just a list of numbers, it must match the statements
                # found in the code.
                self.assertEqual(analysis.statements, lines)
            else:
                # lines is a list of possible line number lists, one of them
                # must match.
                for line_list in lines:
                    if analysis.statements == line_list:
                        break
                else:
                    self.fail("None of the lines choices matched %r" %
                                                        analysis.statements
                        )

            if missing is not None:
                if type(missing) == type(""):
                    self.assertEqual(analysis.missing_formatted(), missing)
                else:
                    for missing_list in missing:
                        if analysis.missing == missing_list:
                            break
                    else:
                        self.fail("None of the missing choices matched %r" %
                                                analysis.missing_formatted()
                            )

        if arcs is not None:
            self.assertEqualArcs(analysis.arc_possibilities(), arcs)

            if arcs_missing is not None:
                self.assertEqualArcs(analysis.arcs_missing(), arcs_missing)

            if arcs_unpredicted is not None:
                self.assertEqualArcs(
                    analysis.arcs_unpredicted(), arcs_unpredicted
                    )

        if report:
            frep = StringIO()
            cov.report(mod, file=frep)
            rep = " ".join(frep.getvalue().split("\n")[2].split()[1:])
            self.assertEqual(report, rep)

    def nice_file(self, *fparts):
        """Canonicalize the filename composed of the parts in `fparts`."""
        fname = os.path.join(*fparts)
        return os.path.normcase(os.path.abspath(os.path.realpath(fname)))

    def command_line(self, args, ret=OK, _covpkg=None):
        """Run `args` through the command line.

        Use this when you want to run the full coverage machinery, but in the
        current process.  Exceptions may be thrown from deep in the code.
        Asserts that `ret` is returned by `CoverageScript.command_line`.

        Compare with `run_command`.

        Returns None.

        """
        script = coverage.CoverageScript(_covpkg=_covpkg)
        ret_actual = script.command_line(shlex.split(args))
        self.assertEqual(ret_actual, ret)

    def run_command(self, cmd):
        """Run the command-line `cmd` in a subprocess, and print its output.

        Use this when you need to test the process behavior of coverage.

        Compare with `command_line`.

        Returns the process' stdout text.

        """
        # Add our test modules directory to PYTHONPATH.  I'm sure there's too
        # much path munging here, but...
        here = os.path.dirname(self.nice_file(coverage.__file__, ".."))
        testmods = self.nice_file(here, 'test/modules')
        zipfile = self.nice_file(here, 'test/zipmods.zip')
        pypath = self.original_environ('PYTHONPATH')
        if pypath:
            pypath += os.pathsep
        pypath += testmods + os.pathsep + zipfile
        self.set_environ('PYTHONPATH', pypath)

        _, output = run_command(cmd)
        print(output)
        return output
