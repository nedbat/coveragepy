import logging
import unittest, os
from nose.plugins import Plugin, PluginTester

import sys
import os
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '../../')))

log = logging.getLogger(__name__)


class Coverage(Plugin):
    """
    Activate a coverage report using Ned Batchelder's coverage module.
    """
    
    name = "coverage_new"
    score = 1
    status = {}
    
    def options(self, parser, env):
        """
        Add options to command line.
        """
        
        Plugin.options(self, parser, env)
        
        from coverage.runner import Options
        # Loop the coverage options and append them to the plugin options
        options = [a for a in dir(Options) if not a.startswith('_')]
        for option in options:
            opt = getattr(Options, option)
            parser.add_option(opt)
    
    def configure(self, options, config):
        """
        Configure plugin.
        """
        try:
            self.status.pop('active')
        except KeyError:
            pass
        Plugin.configure(self, options, config)
        if self.enabled:
            try:
                import coverage
            except ImportError:
                log.error("Coverage not available: "
                          "unable to import coverage module")
                self.enabled = False
                return
        
        self.config = config
        self.status['active'] = True
        self.options = options
        
    def begin(self):
        """
        Begin recording coverage information.
        """
        log.debug("Coverage begin")
        # Load the runner and start it up
        from coverage.runner import CoverageTestWrapper
        self.coverage = CoverageTestWrapper(self.options)
        self.coverage.start()
        
    def report(self, stream):
        """
        Output code coverage report.
        """
        log.debug("Coverage report")
        stream.write("Processing Coverage...")
        # finish up with coverage
        self.coverage.finish()


# Monkey patch omit_filter to use regex patterns for file omits
def omit_filter(omit_prefixes, code_units):
    import re
    exclude_patterns = [re.compile(line.strip()) for line in omit_prefixes if line and not line.startswith('#')]
    filtered = []
    for cu in code_units:
        skip = False
        for pattern in exclude_patterns:
            if pattern.search(cu.filename):
                skip = True
                break
            
        if not skip:
            filtered.append(cu)
    return filtered

try:
    import coverage
    coverage.codeunit.omit_filter = omit_filter
except:
    pass

class TestCoverage(PluginTester, unittest.TestCase):
    activate = '--with-coverage_new' # enables the plugin
    plugins = [Coverage()]
    args = ['--cover-action=report']
    
    def test_output(self):
        assert "Processing Coverage..." in self.output, (
                                        "got: %s" % self.output)
    def makeSuite(self):
        class TC(unittest.TestCase):
            def runTest(self):
                raise ValueError("Coverage down")
        return unittest.TestSuite([TC()])