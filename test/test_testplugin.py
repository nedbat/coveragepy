import py
import unittest
from nose.plugins import PluginTester
from coverage.runners.noseplugin import Coverage

class TestCoverage(PluginTester, unittest.TestCase):
    activate = '--with-coverage' # enables the plugin
    plugins = [Coverage()]
    args = ['--cover-report=report']

    @py.test.mark.skipif(True) # "requires nose test runner"
    def test_output(self):
        assert "Processing Coverage..." in self.output, (
                                        "got: %s" % self.output)
    def makeSuite(self):
        class TC(unittest.TestCase):
            def runTest(self):
                raise ValueError("Coverage down")
        return unittest.TestSuite([TC()])


pytest_plugins = ['pytester']
def test_functional(testdir):
    testdir.makepyfile("""
        def f():
            x = 42
        def test_whatever():
            pass
        """)
    result = testdir.runpytest("--cover-report=annotate")
    assert result.ret == 0
    assert result.stdout.fnmatch_lines([
        '*Processing Coverage*'
        ])
    coveragefile = testdir.tmpdir.join(".coverage")
    assert coveragefile.check()
    # XXX try loading it?
