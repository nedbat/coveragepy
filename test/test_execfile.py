"""Tests for coverage.execfile"""

import os, sys

from coverage.execfile import run_python_file

sys.path.insert(0, os.path.split(__file__)[0]) # Force relative import for Py3k
from coveragetest import CoverageTest

here = os.path.dirname(__file__)

class RunTest(CoverageTest):
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
            fpy.write(nl.join(pylines).encode('utf-8'))
            fpy.close()
            run_python_file('nl.py', ['nl.py'])
        self.assertEqual(self.stdout(), "Hello, world!\n"*3)

