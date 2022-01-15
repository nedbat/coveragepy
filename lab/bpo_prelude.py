import linecache, sys

def trace(frame, event, arg):
    # The weird globals here is to avoid a NameError on shutdown...
    if frame.f_code.co_filename == globals().get("__file__"):
        lineno = frame.f_lineno
        line = linecache.getline(__file__, lineno).rstrip()
        print("{} {}: {}".format(event[:4], lineno, line))
    return trace

print(sys.version)
sys.settrace(trace)

