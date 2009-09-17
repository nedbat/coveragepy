# Test that the --timid command line argument properly swaps the tracer function
# for a simpler one.
#
# This is complicated by the fact that alltests.cmd will run the test suite
# twice for each version: once with a compiled C-based trace function, and once
# without it, to also test the Python trace function.  So this test has to
# examine an environment variable set in alltests.cmd to know whether to expect
# to see the C trace function or not.

import os

copy("src", "out")
run("""
    coverage -e -x showtrace.py regular
    coverage -e -x --timid showtrace.py timid
    """, rundir="out", outfile="showtraceout.txt")

# When running timidly, the trace function is always Python.
contains("out/showtraceout.txt", "timid PyTracer")

if os.environ.get('COVERAGE_TEST_TRACER', 'c') == 'c':
    # If the C trace function is being tested, then regular running should have
    # the C function (shown as None in f_trace since it isn't a Python
    # function).
    contains("out/showtraceout.txt", "regular None")
else:
    # If the Python trace function is being tested, then regular running will
    # also show the Python function.
    contains("out/showtraceout.txt", "regular PyTracer")

# Try the environment variable.
old_opts = os.environ.get('COVERAGE_OPTIONS')
os.environ['COVERAGE_OPTIONS'] = '--timid'

run("""
    coverage -e -x showtrace.py regular
    coverage -e -x --timid showtrace.py timid
    """, rundir="out", outfile="showtraceout.txt")

contains("out/showtraceout.txt",
        "timid PyTracer",
        "regular PyTracer"
        )

if old_opts:
    os.environ['COVERAGE_OPTIONS'] = old_opts
else:
    del os.environ['COVERAGE_OPTIONS']

clean("out")
