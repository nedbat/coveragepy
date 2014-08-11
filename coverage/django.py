import sys


ALL_TEMPLATE_MAP = {}

def get_line_map(filename):
    if filename not in ALL_TEMPLATE_MAP:
        with open(filename) as template_file:
            template_source = template_file.read()
        line_lengths = [len(l) for l in template_source.splitlines(True)]
        ALL_TEMPLATE_MAP[filename] = list(running_sum(line_lengths))
    return ALL_TEMPLATE_MAP[filename]

def get_line_number(line_map, offset):
    for lineno, line_offset in enumerate(line_map, start=1):
        if line_offset >= offset:
            return lineno
    return -1

class DjangoTracer(object):
    def should_trace(self, canonical):
        return "/django/template/" in canonical

    def source(self, frame):
        if frame.f_code.co_name != 'render':
            return None
        that = frame.f_locals['self']
        return getattr(that, "source", None)

    def file_name(self, frame):
        source = self.source(frame)
        if not source:
            return None
        return source[0].name.encode(sys.getfilesystemencoding())

    def line_number_range(self, frame):
        source = self.source(frame)
        if not source:
            return -1, -1
        filename = source[0].name
        line_map = get_line_map(filename)
        start = get_line_number(line_map, source[1][0])
        end = get_line_number(line_map, source[1][1])
        if start < 0 or end < 0:
            return -1, -1
        return start, end

def running_sum(seq):
    total = 0
    for num in seq:
        total += num
        yield total

def ppp(obj):
    ret = []
    import inspect
    for name, value in inspect.getmembers(obj):
        if not callable(value):
            ret.append("%s=%r" % (name, value))
    attrs = ", ".join(ret)
    return "%s: %s" % (obj.__class__, attrs)
