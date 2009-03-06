# Coverage-test coverage.py!

import coverage
import test_coverage
import unittest
import sys

print "Testing under Python version:\n", sys.version

coverage.erase()
coverage.start()
coverage.exclude("#pragma: no cover")

# Re-import coverage to get it coverage tested!
covmod = sys.modules['coverage']
del sys.modules['coverage']
import coverage
sys.modules['coverage'] = coverage = covmod

suite = unittest.TestSuite()
suite.addTest(unittest.defaultTestLoader.loadTestsFromNames(["test_coverage"]))

testrunner = unittest.TextTestRunner()
testrunner.run(suite)

coverage.stop()
coverage.report("coverage.py")
