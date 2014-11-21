"""Plugin management for coverage.py"""

import sys

from coverage.misc import CoverageException


class CoveragePlugin(object):
    """Base class for coverage.py plugins."""
    def __init__(self, options):
        self.options = options

    def file_tracer(self, filename):
        """Return a FileTracer object for this file.

        Every source file is offered to the plugin to give it a chance to take
        responsibility for tracing the file.  If your plugin can handle the
        file, then return a `FileTracer` object.  Otherwise return None.

        There is no way to register your plugin for particular files.  This
        method is how your plugin applies itself to files.  Be prepared for
        `filename` to refer to all kinds of files that have nothing to do with
        your plugin.

        Arguments:
            filename (str): The path to the file being considered.  This is the
                absolute real path to the file.  If you are comparing to other
                paths, be sure to take this into account.

        Returns:
            FileTracer: the `FileTracer` object to use to trace this file, or
                None if this plugin cannot trace this file.

        """
        return None

    def file_reporter(self, filename):
        """Return the FileReporter class to use for filename.

        This will only be invoked if `filename` returns non-None from
        `file_tracer`.  It's an error to return None.

        """
        raise Exception("Plugin %r needs to implement file_reporter" % self.plugin_name)


class FileTracer(object):
    """Support needed for files during the tracing phase."""

    def source_filename(self):
        return "xyzzy"

    def dynamic_source_file_name(self):
        """Returns a callable that can return a source name for a frame.

        The callable should take a filename and a frame, and return either a
        filename or None:

            def dynamic_source_filename_func(filename, frame)

        Can return None if dynamic filenames aren't needed.

        """
        return None

    def line_number_range(self, frame):
        """Given a call frame, return the range of source line numbers.

        The call frame is examined, and the source line number in the original
        file is returned.  The return value is a pair of numbers, the starting
        line number and the ending line number, both inclusive.  For example,
        returning (5, 7) means that lines 5, 6, and 7 should be considered
        executed.

        This function might decide that the frame doesn't indicate any lines
        from the source file were executed.  Return (-1, -1) in this case to
        tell coverage.py that no lines should be recorded for this frame.

        Arguments:
            frame: the call frame to examine.

        Returns:
            (int, int): a pair of line numbers, the start and end lines
                executed in the source, inclusive.

        """
        lineno = frame.f_lineno
        return lineno, lineno


class FileReporter(object):
    """Support needed for files during the reporting phase."""
    def __init__(self, filename):
        self.filename = filename


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
                plugin.plugin_name = module
                plugins.order.append(plugin)
                plugins.names[module] = plugin

        return plugins

    def __iter__(self):
        return iter(self.order)

    def get(self, module):
        return self.names[module]
