from coverage.execfile import run_python_file
import cStringIO, os, sys, unittest

here = os.path.dirname(__file__)

class RunTests(unittest.TestCase):
    def setUp(self):
        self.oldstdout = sys.stdout
        self.stdout = sys.stdout = cStringIO.StringIO()
        
    def tearDown(self):
        self.stdout = self.oldstdout

    def test_run_python_file(self):
        tryfile = os.path.join(here, "try_execfile.py")
        run_python_file(tryfile)
        mod_globs = eval(self.stdout.getvalue())
        self.assertEqual(mod_globs['__name__'], "__main__")
        self.assertEqual(os.path.basename(mod_globs['__file__']), "try_execfile.py")
