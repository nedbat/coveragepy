import sys

pairs = set()
last = -1

def trace(frame, event, arg):
    global last
    if event == "line":
        this = frame.f_lineno
        pairs.add((last, this))
        last = this
    return trace

code = open(sys.argv[1]).read()
sys.settrace(trace)
exec(code)
print(sorted(pairs))
