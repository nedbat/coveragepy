"""A plugin for test_plugins.py to import."""

import os.path

import coverage


class Plugin(coverage.CoveragePlugin):
    """A plugin to import, so that it isn't in the test's current directory."""

    def file_tracer(self, filename):
        """Trace only files named xyz.py"""
        if "xyz.py" in filename:
            return FileTracer(filename)

    def file_reporter(self, filename):
        return FileReporter(filename)


class FileTracer(coverage.plugin.FileTracer):
    """A FileTracer emulating a simple static plugin."""

    def __init__(self, filename):
        """Claim that xyz.py was actually sourced from ABC.zz"""
        self._filename = filename
        self._source_filename = os.path.join(
            "/src",
            os.path.basename(filename.replace("xyz.py", "ABC.zz"))
        )

    def source_filename(self):
        return self._source_filename

    def line_number_range(self, frame):
        """Map the line number X to X05,X06,X07."""
        lineno = frame.f_lineno
        return lineno*100+5, lineno*100+7


class FileReporter(coverage.plugin.FileReporter):
    """Dead-simple FileReporter."""
    def statements(self):
        return set([105, 106, 107, 205, 206, 207])

    def excluded_statements(self):
        return set([])


def coverage_init(reg, options):
    """Called by coverage to initialize the plugins here."""
    reg.add_file_tracer(Plugin())
