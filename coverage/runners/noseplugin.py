"""A nose plugin to run coverage.py"""

import logging
from nose.plugins import Plugin

from coverage.runners.plugin import CoverageTestWrapper, options as coverage_opts


log = logging.getLogger(__name__)


class Coverage(Plugin):
    """Nose plugin for coverage reporting."""

    score = 1
    status = {}

    def options(self, parser, env):
        """Add command-line options."""

        super(Coverage, self).options(parser, env)
        for opt in coverage_opts:
            parser.add_option(opt)

    def configure(self, options, config):
        """Configure plugin."""

        try:
            self.status.pop('active')
        except KeyError:
            pass

        super(Coverage, self).configure(options, config)

        self.config = config
        self.status['active'] = True
        self.options = options

    def begin(self):
        """Begin recording coverage information."""

        log.debug("Coverage begin")
        self.coverage = CoverageTestWrapper(self.options)
        self.coverage.start()

    def report(self, stream):
        """Output code coverage report."""

        log.debug("Coverage report")
        stream.write("Processing Coverage...")
        self.coverage.finish(stream)
