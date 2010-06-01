"""py.test plugin hooks"""

from coverage.runners.plugin import CoverageTestWrapper, OPTIONS

def pytest_addoption(parser):
    """Get all the options from the coverage.runner and import them."""
    group = parser.getgroup('Coverage options')
    for opt in OPTIONS:
        group._addoption_instance(opt)

def pytest_configure(config):
    """Load the runner and start it up."""
    if config.getvalue("cover_actions"):
        config.pluginmanager.register(CoveragePlugin(config), "do_coverage")

class CoveragePlugin:
    """The py.test coverage plugin."""

    def __init__(self, config):
        self.config = config

    def pytest_sessionstart(self):
        """Called before session.main() is called."""
        self.coverage = CoverageTestWrapper(self.config.option)
        # XXX maybe better to start/suspend/resume coverage
        # for each single test item
        self.coverage.start()

    def pytest_terminal_summary(self, terminalreporter):
        """Add an additional section in the terminal summary reporting."""
        tw = terminalreporter._tw
        tw.sep('-', 'coverage')
        tw.line('Processing Coverage...')
        self.coverage.finish()
