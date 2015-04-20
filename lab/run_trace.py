"""Run a simple trace function on a file of Python code."""

import os, sys

nest = 0

def trace(frame, event, arg):
    global nest

    if nest is None:
        # This can happen when Python is shutting down.
        return None

    print "%s%s %s %d @%d" % (
        "    " * nest,
        event,
        os.path.basename(frame.f_code.co_filename),
        frame.f_lineno,
        frame.f_lasti,
        )

    if event == 'call':
        nest += 1
    if event == 'return':
        nest -= 1

    return trace

the_program = sys.argv[1]

sys.settrace(trace)
execfile(the_program)
