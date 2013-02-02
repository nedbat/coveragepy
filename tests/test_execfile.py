"""Tests for coverage.execfile"""

import os, sys

from coverage.execfile import run_python_file, run_python_module
from coverage.misc import NoSource

from test.coveragetest import CoverageTest

here = os.path.dirname(__file__)

class RunFileTest(CoverageTest):
    """Test cases for `run_python_file`."""

    def test_run_python_file(self):
        tryfile = os.path.join(here, "try_execfile.py")
        run_python_file(tryfile, [tryfile, "arg1", "arg2"])
        mod_globs = eval(self.stdout())

        # The file should think it is __main__
        self.assertEqual(mod_globs['__name__'], "__main__")

        # It should seem to come from a file named try_execfile.py
        dunder_file = os.path.basename(mod_globs['__file__'])
        self.assertEqual(dunder_file, "try_execfile.py")

        # It should have its correct module data.
        self.assertEqual(mod_globs['__doc__'],
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
            fpy = open('nl.py', 'wb')
            try:
                fpy.write(nl.join(pylines).encode('utf-8'))
            finally:
                fpy.close()
            run_python_file('nl.py', ['nl.py'])
        self.assertEqual(self.stdout(), "Hello, world!\n"*3)

    def test_missing_final_newline(self):
        # Make sure we can deal with a Python file with no final newline.
        self.make_file("abrupt.py", """\
            if 1:
                a = 1
                print("a is %r" % a)
                #""")
        abrupt = open("abrupt.py").read()
        self.assertEqual(abrupt[-1], '#')
        run_python_file("abrupt.py", ["abrupt.py"])
        self.assertEqual(self.stdout(), "a is 1\n")

    def test_no_such_file(self):
        self.assertRaises(NoSource, run_python_file, "xyzzy.py", [])


class RunModuleTest(CoverageTest):
    """Test run_python_module."""

    run_in_temp_dir = False

    def setUp(self):
        super(RunModuleTest, self).setUp()
        # Parent class saves and restores sys.path, we can just modify it.
        sys.path.append(self.nice_file(os.path.dirname(__file__), 'modules'))

    def test_runmod1(self):
        run_python_module("runmod1", ["runmod1", "hello"])
        self.assertEqual(self.stdout(), "runmod1: passed hello\n")

    def test_runmod2(self):
        run_python_module("pkg1.runmod2", ["runmod2", "hello"])
        self.assertEqual(self.stdout(), "runmod2: passed hello\n")

    def test_runmod3(self):
        run_python_module("pkg1.sub.runmod3", ["runmod3", "hello"])
        self.assertEqual(self.stdout(), "runmod3: passed hello\n")

    def test_pkg1_main(self):
        run_python_module("pkg1", ["pkg1", "hello"])
        self.assertEqual(self.stdout(), "pkg1.__main__: passed hello\n")

    def test_pkg1_sub_main(self):
        run_python_module("pkg1.sub", ["pkg1.sub", "hello"])
        self.assertEqual(self.stdout(), "pkg1.sub.__main__: passed hello\n")

    def test_no_such_module(self):
        self.assertRaises(NoSource, run_python_module, "i_dont_exist", [])
        self.assertRaises(NoSource, run_python_module, "i.dont_exist", [])
        self.assertRaises(NoSource, run_python_module, "i.dont.exist", [])

    def test_no_main(self):
        self.assertRaises(NoSource, run_python_module, "pkg2", ["pkg2", "hi"])
