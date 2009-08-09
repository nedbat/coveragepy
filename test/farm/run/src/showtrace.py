# Show the current frame's trace function, so that we can test what the
# command-line options do to the trace function used.

import sys

# Print the argument as a label for the output.
print sys.argv[1],

# Show what the trace function is.  If a C-based function is used, then f_trace
# is None.
trace_fn = sys._getframe(0).f_trace
if trace_fn is None:
    print "None"
else:
    print trace_fn.im_class
