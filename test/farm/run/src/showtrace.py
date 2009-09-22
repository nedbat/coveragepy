# Show the current frame's trace function, so that we can test what the
# command-line options do to the trace function used.

import sys

# Show what the trace function is.  If a C-based function is used, then f_trace
# is None.
trace_fn = sys._getframe(0).f_trace
if trace_fn is None:
    trace_name = "None"
else:
    # Get the name of the tracer class.  Py3k has a different way to get it.
    try:
        trace_name = trace_fn.im_class.__name__
    except AttributeError:
        trace_name = trace_fn.__self__.__class__.__name__

print("%s %s" % (sys.argv[1], trace_name))
