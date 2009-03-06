# File-based unit tests for coverage.py

import path, sys, unittest
import coverage

class OneFileTestCase(unittest.TestCase):
    def __init__(self, filename):
        unittest.TestCase.__init__(self)
        self.filename = filename

    def shortDescription(self):
        return self.filename

    def setUp(self):
        # Create a temporary directory.
        self.noise = str(random.random())[2:]
        self.temproot = path.path(tempfile.gettempdir()) / 'test_coverage' 
        self.tempdir = self.temproot / self.noise
        self.tempdir.makedirs()
        self.olddir = os.getcwd()
        os.chdir(self.tempdir)
        # Keep a counter to make every call to checkCoverage unique.
        self.n = 0

        # Capture stdout, so we can use print statements in the tests and not
        # pollute the test output.
        self.oldstdout = sys.stdout
        self.capturedstdout = StringIO()
        sys.stdout = self.capturedstdout
        coverage.begin_recursive()
        
    def tearDown(self):
        coverage.end_recursive()
        sys.stdout = self.oldstdout
        # Get rid of the temporary directory.
        os.chdir(self.olddir)
        self.temproot.rmtree()
    
    def runTest(self):
        # THIS ISN'T DONE YET!
        pass

class MyTestSuite(unittest.TestSuite):
    def __init__(self):
        unittest.TestSuite.__init__(self)
        for f in path.path('test').walk('*.py'):
            self.addFile(f)
                    
    def addFile(self, f):
        self.addTest(OneFileTestCase(f))

if __name__ == '__main__':
    unittest.main(defaultTest='MyTestSuite')
