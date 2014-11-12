"""Plugins for test_plugins.py to import."""

import os.path

import coverage
from coverage.parser import CodeParser


class Plugin(coverage.CoveragePlugin):
    """A plugin to import, so that it isn't in the test's current directory."""

    def file_tracer(self, filename):
        """Trace only files named xyz.py"""
        if "xyz.py" in filename:
            file_tracer = FileTracer(filename)
            return file_tracer

    def file_reporter(self, filename):
        return FileReporter(filename)


class FileTracer(coverage.plugin.FileTracer):
    def __init__(self, filename):
        """xyz.py was actually sourced from ABC.zz"""
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
    def get_parser(self, exclude=None):
        return PluginParser()

class PluginParser(CodeParser):
    def parse_source(self):
        return set([105, 106, 107, 205, 206, 207]), set([])
