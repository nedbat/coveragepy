from coverage.execfile import run_python_file
import cStringIO, os, sys, unittest

here = os.path.dirname(__file__)

class Tee(object):
    def __init__(self, *files):
        self.files = files
        
    def write(self, data):
        for f in self.files:
            f.write(data)

class RunTest(unittest.TestCase):
    def setUp(self):
        self.oldstdout = sys.stdout
        self.stdout = cStringIO.StringIO()
        sys.stdout = Tee(sys.stdout, self.stdout)
        
    def tearDown(self):
        self.stdout = self.oldstdout

    def test_run_python_file(self):
        tryfile = os.path.join(here, "try_execfile.py")
        run_python_file(tryfile, [tryfile, "arg1", "arg2"])
        mod_globs = eval(self.stdout.getvalue())
        
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
