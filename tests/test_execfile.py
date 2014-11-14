"""Tests for coverage.execfile"""

import compileall, json, os, re, sys

from coverage.backward import binary_bytes
from coverage.execfile import run_python_file, run_python_module
from coverage.misc import NoCode, NoSource

from tests.coveragetest import CoverageTest

here = os.path.dirname(__file__)

class RunFileTest(CoverageTest):
    """Test cases for `run_python_file`."""

    def test_run_python_file(self):
        tryfile = os.path.join(here, "try_execfile.py")
        run_python_file(tryfile, [tryfile, "arg1", "arg2"])
        mod_globs = json.loads(self.stdout())

        # The file should think it is __main__
        self.assertEqual(mod_globs['__name__'], "__main__")

        # It should seem to come from a file named try_execfile.py
        dunder_file = os.path.basename(mod_globs['__file__'])
        self.assertEqual(dunder_file, "try_execfile.py")

        # It should have its correct module data.
        self.assertEqual(mod_globs['__doc__'].splitlines()[0],
                            "Test file for run_python_file.")
        self.assertEqual(mod_globs['DATA'], "xyzzy")
        self.assertEqual(mod_globs['FN_VAL'], "my_fn('fooey')")

        # It must be self-importable as __main__.
        self.assertEqual(mod_globs['__main__.DATA'], "xyzzy")

        # Argv should have the proper values.
        self.assertEqual(mod_globs['argv'], [tryfile, "arg1", "arg2"])

        # __builtins__ should have the right values, like open().
        self.assertEqual(mod_globs['__builtins__.has_open'], True)

    def test_no_extra_file(self):
        # Make sure that running a file doesn't create an extra compiled file.
        self.make_file("xxx", """\
            desc = "a non-.py file!"
            """)

        self.assertEqual(os.listdir("."), ["xxx"])
        run_python_file("xxx", ["xxx"])
        self.assertEqual(os.listdir("."), ["xxx"])

    def test_universal_newlines(self):
        # Make sure we can read any sort of line ending.
        pylines = """# try newlines|print('Hello, world!')|""".split('|')
        for nl in ('\n', '\r\n', '\r'):
            with open('nl.py', 'wb') as fpy:
                fpy.write(nl.join(pylines).encode('utf-8'))
            run_python_file('nl.py', ['nl.py'])
        self.assertEqual(self.stdout(), "Hello, world!\n"*3)

    def test_missing_final_newline(self):
        # Make sure we can deal with a Python file with no final newline.
        self.make_file("abrupt.py", """\
            if 1:
                a = 1
                print("a is %r" % a)
                #""")
        with open("abrupt.py") as f:
            abrupt = f.read()
        self.assertEqual(abrupt[-1], '#')
        run_python_file("abrupt.py", ["abrupt.py"])
        self.assertEqual(self.stdout(), "a is 1\n")

    def test_no_such_file(self):
        with self.assertRaises(NoSource):
            run_python_file("xyzzy.py", [])


class RunPycFileTest(CoverageTest):
    """Test cases for `run_python_file`."""

    def make_pyc(self):
        """Create a .pyc file, and return the relative path to it."""
        self.make_file("compiled.py", """\
            def doit():
                print("I am here!")

            doit()
            """)
        compileall.compile_dir(".", quiet=True)
        os.remove("compiled.py")

        # Find the .pyc file!
        for there, _, files in os.walk("."):            # pragma: part covered
            for f in files:
                if f.endswith(".pyc"):                  # pragma: part covered
                    return os.path.join(there, f)

    def test_running_pyc(self):
        pycfile = self.make_pyc()
        run_python_file(pycfile, [pycfile])
        self.assertEqual(self.stdout(), "I am here!\n")

    def test_running_pyo(self):
        pycfile = self.make_pyc()
        pyofile = re.sub(r"[.]pyc$", ".pyo", pycfile)
        self.assertNotEqual(pycfile, pyofile)
        os.rename(pycfile, pyofile)
        run_python_file(pyofile, [pyofile])
        self.assertEqual(self.stdout(), "I am here!\n")

    def test_running_pyc_from_wrong_python(self):
        pycfile = self.make_pyc()

        # Jam Python 2.1 magic number into the .pyc file.
        with open(pycfile, "r+b") as fpyc:
            fpyc.seek(0)
            fpyc.write(binary_bytes([0x2a, 0xeb, 0x0d, 0x0a]))

        with self.assertRaisesRegex(NoCode, "Bad magic number in .pyc file"):
            run_python_file(pycfile, [pycfile])

    def test_no_such_pyc_file(self):
        with self.assertRaisesRegex(NoCode, "No file to run: 'xyzzy.pyc'"):
            run_python_file("xyzzy.pyc", [])


class RunModuleTest(CoverageTest):
    """Test run_python_module."""

    run_in_temp_dir = False

    def setUp(self):
        super(RunModuleTest, self).setUp()
        # Parent class saves and restores sys.path, we can just modify it.
        sys.path.append(self.nice_file(os.path.dirname(__file__), 'modules'))

    def test_runmod1(self):
        run_python_module("runmod1", ["runmod1", "hello"])
        self.assertEqual(self.stderr(), "")
        self.assertEqual(self.stdout(), "runmod1: passed hello\n")

    def test_runmod2(self):
        run_python_module("pkg1.runmod2", ["runmod2", "hello"])
        self.assertEqual(self.stderr(), "")
        self.assertEqual(self.stdout(), "runmod2: passed hello\n")

    def test_runmod3(self):
        run_python_module("pkg1.sub.runmod3", ["runmod3", "hello"])
        self.assertEqual(self.stderr(), "")
        self.assertEqual(self.stdout(), "runmod3: passed hello\n")

    def test_pkg1_main(self):
        run_python_module("pkg1", ["pkg1", "hello"])
        self.assertEqual(self.stderr(), "")
        self.assertEqual(self.stdout(), "pkg1.__main__: passed hello\n")

    def test_pkg1_sub_main(self):
        run_python_module("pkg1.sub", ["pkg1.sub", "hello"])
        self.assertEqual(self.stderr(), "")
        self.assertEqual(self.stdout(), "pkg1.sub.__main__: passed hello\n")

    def test_no_such_module(self):
        with self.assertRaises(NoSource):
            run_python_module("i_dont_exist", [])
        with self.assertRaises(NoSource):
            run_python_module("i.dont_exist", [])
        with self.assertRaises(NoSource):
            run_python_module("i.dont.exist", [])

    def test_no_main(self):
        with self.assertRaises(NoSource):
            run_python_module("pkg2", ["pkg2", "hi"])
