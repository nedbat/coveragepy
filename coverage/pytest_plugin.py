"""
PYTEST_DONT_REWRITE
"""
import argparse


def validate_context(arg):
    if arg != "test":
        msg = '--cov-context=test is the only supported value'
        raise argparse.ArgumentTypeError(msg)
    return arg


def pytest_addoption(parser):
    try:
        import pytest_cov
    except ImportError:
        pass
    else:
        group = parser.getgroup('cov', 'coverage reporting with distributed testing support')
        group.addoption('--cov-context', action='store', metavar='CONTEXT',
                        type=validate_context,
                        help='Dynamic context to use. Available contexts: only "test" for now.')


def pytest_sessionstart(session):
    config = session.config
    cov = config.pluginmanager.get_plugin('_cov')
    if (
        config.known_args_namespace.cov_context == 'test'
        and cov
        and cov.cov_controller
        and config.known_args_namespace.cov_source
    ):
        config.pluginmanager.register(TestContextPlugin(cov.cov_controller.cov), '_cov_contexts')


class TestContextPlugin(object):
    def __init__(self, cov):
        self.cov = cov

    def pytest_runtest_setup(self, item):
        self.switch_context(item, 'setup')

    def pytest_runtest_teardown(self, item):
        self.switch_context(item, 'teardown')

    def pytest_runtest_call(self, item):
        self.switch_context(item, 'run')

    def switch_context(self, item, when):
        context = "{item.nodeid}|{when}".format(item=item, when=when)
        self.cov.switch_context(context)
