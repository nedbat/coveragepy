"""Plugin management for coverage.py"""

import sys


class CoveragePlugin(object):
    """Base class for coverage.py plugins."""
    def __init__(self, options):
        self.options = options

    def trace_judge(self):
        """Return a callable that can decide whether to trace a file or not.

        The callable should take a filename, and return a coverage.TraceDisposition
        object.

        """
        return None

    # TODO: why does trace_judge return a callable, but source_file_name is callable?
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
            plugin.__name__ = module
            plugins.append(plugin)

    return plugins
