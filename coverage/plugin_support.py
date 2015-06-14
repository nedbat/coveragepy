"""Support for plugins."""

import sys

from coverage.misc import CoverageException
from coverage.plugin import CoveragePlugin, FileTracer, FileReporter


class Plugins(object):
    """The currently loaded collection of coverage.py plugins."""

    def __init__(self):
        self.order = []
        self.names = {}

    @classmethod
    def load_plugins(cls, modules, config, debug=None):
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
            if debug and debug.should('plugin'):
                debug.write("Loaded plugin %r: %r" % (module, plugin))
                labelled = LabelledDebug("plugin %r" % (module,), debug)
                plugin = DebugPluginWrapper(plugin, labelled)
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


class LabelledDebug(object):
    """A Debug writer, but with labels for prepending to the messages."""

    def __init__(self, label, debug, prev_labels=()):
        self.labels = list(prev_labels) + [label]
        self.debug = debug

    def add_label(self, label):
        """Add a label to the writer, and return a new `LabelledDebug`."""
        return LabelledDebug(label, self.debug, self.labels)

    def write(self, message):
        """Write `message`, but with the labels prepended."""
        self.debug.write("%s: %s" % (", ".join(self.labels), message))


class DebugPluginWrapper(CoveragePlugin):
    """Wrap a plugin, and use debug to report on what it's doing."""

    def __init__(self, plugin, debug):
        super(DebugPluginWrapper, self).__init__()
        self.plugin = plugin
        self.debug = debug

    def file_tracer(self, filename):
        tracer = self.plugin.file_tracer(filename)
        self.debug.write("file_tracer(%r) --> %r" % (filename, tracer))
        if tracer:
            debug = self.debug.add_label("file %r" % (filename,))
            tracer = DebugFileTracerWrapper(tracer, debug)
        return tracer

    def file_reporter(self, filename):
        reporter = self.plugin.file_reporter(filename)
        self.debug.write("file_reporter(%r) --> %r" % (filename, reporter))
        if reporter:
            debug = self.debug.add_label("file %r" % (filename,))
            reporter = DebugFileReporterWrapper(filename, reporter, debug)
        return reporter

    def sys_info(self):
        return self.plugin.sys_info()


class DebugFileTracerWrapper(FileTracer):
    """A debugging `FileTracer`."""

    def __init__(self, tracer, debug):
        self.tracer = tracer
        self.debug = debug

    def source_filename(self):
        sfilename = self.tracer.source_filename()
        self.debug.write("source_filename() --> %r" % (sfilename,))
        return sfilename

    def has_dynamic_source_filename(self):
        has = self.tracer.has_dynamic_source_filename()
        self.debug.write("has_dynamic_source_filename() --> %r" % (has,))
        return has

    def dynamic_source_filename(self, filename, frame):
        dyn = self.tracer.dynamic_source_filename(filename, frame)
        self.debug.write("dynamic_source_filename(%r, frame) --> %r" % (filename, dyn))
        return dyn

    def line_number_range(self, frame):
        pair = self.tracer.line_number_range(frame)
        self.debug.write("line_number_range(frame) --> %r" % (pair,))
        return pair


class DebugFileReporterWrapper(FileReporter):
    """A debugging `FileReporter`."""

    def __init__(self, filename, reporter, debug):
        super(DebugFileReporterWrapper, self).__init__(filename)
        self.reporter = reporter
        self.debug = debug

    def relative_filename(self):
        ret = self.reporter.relative_filename()
        self.debug.write("relative_filename() --> %r" % (ret,))
        return ret

    def statements(self):
        ret = self.reporter.statements()
        self.debug.write("statements() --> %r" % (ret,))
        return ret

    def excluded_statements(self):
        ret = self.reporter.excluded_statements()
        self.debug.write("excluded_statements() --> %r" % (ret,))
        return ret

    def translate_lines(self, lines):
        ret = self.reporter.translate_lines(lines)
        self.debug.write("translate_lines(%r) --> %r" % (lines, ret))
        return ret

    def translate_arcs(self, arcs):
        ret = self.reporter.translate_arcs(arcs)
        self.debug.write("translate_arcs(%r) --> %r" % (arcs, ret))
        return ret

    def no_branch_lines(self):
        ret = self.reporter.no_branch_lines()
        self.debug.write("no_branch_lines() --> %r" % (ret,))
        return ret

    def exit_counts(self):
        ret = self.reporter.exit_counts()
        self.debug.write("exit_counts() --> %r" % (ret,))
        return ret

    def arcs(self):
        ret = self.reporter.arcs()
        self.debug.write("arcs() --> %r" % (ret,))
        return ret

    def source(self):
        ret = self.reporter.source()
        self.debug.write("source() --> %d chars" % (len(ret),))
        return ret

    def source_token_lines(self):
        ret = list(self.reporter.source_token_lines())
        self.debug.write("source_token_lines() --> %d tokens" % (len(ret),))
        return ret

    def should_be_python(self):
        ret = self.reporter.should_be_python()
        self.debug.write("should_be_python() --> %r" % (ret,))
        return ret
