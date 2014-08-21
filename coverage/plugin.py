"""Plugin management for coverage.py"""

import sys


class CoveragePlugin(object):
    """Base class for coverage.py plugins."""
    def __init__(self, options):
        self.options = options


def load_plugins(modules, config):
    """Load plugins from `modules`.

    Returns a list of loaded and configured plugins.

    """
    plugins = []

    for module in modules:
        __import__(module)
        mod = sys.modules[module]

        plugin_class = getattr(mod, "Plugin", None)
        if plugin_class:
            options = config.get_plugin_options(module)
            plugin = plugin_class(options)
            plugins.append(plugin)

    return plugins
