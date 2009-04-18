"""Tests for coverage.execfile"""

import os

from coverage.execfile import run_python_file
from coveragetest import CoverageTest

here = os.path.dirname(__file__)

class RunTest(CoverageTest):

    def test_run_python_file(self):
        tryfile = os.path.join(here, "try_execfile.py")
        run_python_file(tryfile, [tryfile, "arg1", "arg2"])
        mod_globs = eval(self.stdout())
        
        # The file should think it is __main__
        self.assertEqual(mod_globs['__name__'], "__main__")

        # It should seem to come from a file named try_execfile
        dunder_file = os.path.splitext(
                        os.path.basename(mod_globs['__file__'])
                        )[0]
        self.assertEqual(dunder_file, "try_execfile")

        # It should have its correct module data.
        self.assertEqual(mod_globs['__doc__'], "Test file for run_python_file.")
        self.assertEqual(mod_globs['DATA'], "xyzzy")
        self.assertEqual(mod_globs['FN_VAL'], "my_fn('fooey')")
        
        # It must be self-importable as __main__.
        self.assertEqual(mod_globs['__main__.DATA'], "xyzzy")
        
        # Argv should have the proper values.
        self.assertEqual(mod_globs['argv'], [tryfile, "arg1", "arg2"])
