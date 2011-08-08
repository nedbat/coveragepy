"""Imposter encodings module that installs a coverage-style tracer.

This is NOT the encodings module; it is an imposter that sets up tracing
instrumentation and then replaces itself with the real encodings module.

If the directory that holds this file is placed first in the PYTHONPATH when
using "coverage" to run Python's tests, then this file will become the very
first module imported by the internals of Python 3.  It installs a
coverage-compatible trace function that can watch Standard Library modules
execute from the very earliest stages of Python's own boot process.  This fixes
a problem with coverage - that it starts too late to trace the coverage of many
of the most fundamental modules in the Standard Library.

"""

import sys

class FullCoverageTracer(object):
    def __init__(self):
        self.traces = []

    def fullcoverage_trace(self, *args):
        frame, event, arg = args
        #if "os.py" in frame.f_code.co_filename:
        #    print("%s @ %d" % (frame.f_code.co_filename, frame.f_lineno))
        self.traces.append(args)
        return self.fullcoverage_trace

sys.settrace(FullCoverageTracer().fullcoverage_trace)

# Finally, remove our own directory from sys.path; remove ourselves from
# sys.modules; and re-import "encodings", which will be the real package
# this time.  Note that the delete from sys.modules dictionary has to
# happen last, since all of the symbols in this module will become None
# at that exact moment, including "sys".

import os
this = os.path.dirname(__file__)
sys.path.remove(this)
del sys.modules['encodings']
import encodings
