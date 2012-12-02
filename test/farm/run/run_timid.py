# Test that the --timid command line argument properly swaps the tracer
# function for a simpler one.
#
# This is complicated by the fact that the tests are run twice for each
# version: once with a compiled C-based trace function, and once without
# it, to also test the Python trace function.  So this test has to examine
# an environment variable set in igor.py to know whether to expect to see
# the C trace function or not.

import os

# When meta-coverage testing, this test doesn't work, because it finds
# coverage.py's own trace function.
if os.environ.get('COVERAGE_COVERAGE', ''):
    skip("Can't test timid during coverage measurement.")

copy("src", "out")
run("""
    python showtrace.py none
    coverage -e -x showtrace.py regular
    coverage -e -x --timid showtrace.py timid
    """, rundir="out", outfile="showtraceout.txt")

# When running without coverage, no trace function
# When running timidly, the trace function is always Python.
contains("out/showtraceout.txt",
    "none None",
    "timid PyTracer",
    )

if os.environ.get('COVERAGE_TEST_TRACER', 'c') == 'c':
    # If the C trace function is being tested, then regular running should have
    # the C function, which registers itself as f_trace.
    contains("out/showtraceout.txt", "regular CTracer")
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
    "none None",
    "timid PyTracer",
    "regular PyTracer",
    )

if old_opts:
    os.environ['COVERAGE_OPTIONS'] = old_opts
else:
    del os.environ['COVERAGE_OPTIONS']

clean("out")
