"""A plugin for test_plugins.py to import."""

import coverage

class Plugin(coverage.CoveragePlugin):
    def file_tracer(self, filename):
        if "render.py" in filename:
            return RenderFileTracer(filename)


class RenderFileTracer(coverage.plugin.FileTracer):
    def __init__(self, filename):
        pass

    def has_dynamic_source_filename(self):
        return True

    def dynamic_source_filename(self, filename, frame):
        filename = "fake%d.html" % frame.f_lineno
        print("dynamic filename: %r" % filename)
        return filename

    def line_number_range(self, frame):
        return 17,19
