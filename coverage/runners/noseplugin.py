"""A nose plugin to run coverage.py"""

import logging
from nose.plugins import Plugin

from coverage.runners.plugin import CoverageTestWrapper, OPTIONS


log = logging.getLogger("nose.plugins.coverage")


class Coverage(Plugin):
    """The nose plugin to measure test coverage."""

    score = 200
    status = {}

    def help(self):
        """The help for the --with-coverage option."""
        return "Measure test coverage using coverage.py."

    def options(self, parser, env):
        """Add command-line options."""

        super(Coverage, self).options(parser, env)
        for opt in OPTIONS:
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
        self.opts = options

    def begin(self):
        """Begin recording coverage information."""

        log.debug("Coverage begin")
        self.coverage = CoverageTestWrapper(self.opts)
        self.coverage.start()

    def report(self, stream):
        """Output code coverage report."""

        log.debug("Coverage report")
        stream.write("Processing Coverage...\n")
        self.coverage.finish(stream)
