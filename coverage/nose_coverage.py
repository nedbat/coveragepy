import logging
import unittest, os
from nose.plugins import Plugin
import sys

from coverage.testplugin import CoverageTestWrapper, options as coverage_opts

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
        for opt in coverage_opts:
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
        self.coverage = CoverageTestWrapper(self.options)
        self.coverage.start()
        
    def report(self, stream):
        """
        Output code coverage report.
        """
        log.debug("Coverage report")
        stream.write("Processing Coverage...")
        # finish up with coverage
        self.coverage.finish(stream)

