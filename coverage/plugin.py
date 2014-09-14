"""Plugin management for coverage.py"""

import sys


class CoveragePlugin(object):
    """Base class for coverage.py plugins."""
    def __init__(self, options):
        self.options = options

    def trace_judge(self, disposition):
        """Decide whether to trace this file with this plugin.

        Set disposition.trace to True if this plugin should trace this file.
        May also set other attributes in `disposition`.

        """
        return None

    def source_file_name(self, filename):
        """Return the source name for a given Python filename.

        Can return None if tracing shouldn't continue.

        """
        return filename

    def dynamic_source_file_name(self):
        """Returns a callable that can return a source name for a frame.

        The callable should take a filename and a frame, and return either a
        filename or None:

            def dynamic_source_filename_func(filename, frame)

        Can return None if dynamic filenames aren't needed.

        """
        return None

    def code_unit_class(self, morf):
        """Return the CodeUnit class to use for a module or filename."""
        return None


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
            if plugin_class:
                options = config.get_plugin_options(module)
                plugin = plugin_class(options)
                plugin.__name__ = module
                plugins.order.append(plugin)
                plugins.names[module] = plugin

        return plugins

    def __iter__(self):
        return iter(self.order)

    def get(self, module):
        return self.names[module]


def overrides(obj, method_name, base_class):
    """Does `obj` override the `method_name` it got from `base_class`?

    Determine if `obj` implements the method called `method_name`, which it
    inherited from `base_class`.

    Returns a boolean.

    """
    klass = obj.__class__
    klass_func = getattr(klass, method_name)
    base_func = getattr(base_class, method_name)

    # Python 2/3 compatibility: Python 2 returns an instancemethod object, the
    # function is the .im_func attribute.  Python 3 returns a plain function
    # object already.
    if sys.version_info < (3, 0):
        klass_func = klass_func.im_func
        base_func = base_func.im_func

    return klass_func is not base_func


def plugin_implements(obj, method_name):
    """Does the plugin `obj` implement `method_name`?"""
    return overrides(obj, method_name, CoveragePlugin)
