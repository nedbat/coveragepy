"""Support for plugins."""

import sys

from coverage.misc import CoverageException


class Plugins(object):
    """The currently loaded collection of coverage.py plugins."""

    def __init__(self):
        self.order = []
        self.names = {}

    @classmethod
    def load_plugins(cls, modules, config):
        """Load plugins from `modules`.

        Returns a list of loaded and configured plugins.

        """
        plugins = cls()

        for module in modules:
            __import__(module)
            mod = sys.modules[module]

            plugin_class = getattr(mod, "Plugin", None)
            if not plugin_class:
                raise CoverageException("Plugin module %r didn't define a Plugin class" % module)

            options = config.get_plugin_options(module)
            plugin = plugin_class(options)
            plugin._coverage_plugin_name = module
            plugin._coverage_enabled = True
            plugins.order.append(plugin)
            plugins.names[module] = plugin

        return plugins

    def __nonzero__(self):
        return bool(self.order)

    __bool__ = __nonzero__

    def __iter__(self):
        return iter(self.order)

    def get(self, plugin_name):
        """Return a plugin by name."""
        return self.names[plugin_name]
