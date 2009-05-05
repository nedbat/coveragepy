"""Code coverage measurement for Python.

Ned Batchelder
http://nedbatchelder.com/code/modules/coverage.html

"""

__version__ = "3.0b3"    # see detailed history in CHANGES

from coverage.control import coverage
from coverage.data import CoverageData
from coverage.cmdline import main, CoverageScript
from coverage.misc import CoverageException


# Module-level functions.  The original API to this module was based on
# functions defined directly in the module, with a singleton of the coverage()
# class.  That design hampered programmability.  Here we define the top-level
# functions to create the singleton when they are first called.

# Singleton object for use with module-level functions.  The singleton is
# created as needed when one of the module-level functions is called.
_the_coverage = None

def _call_singleton_method(name, args, kwargs):
    global _the_coverage
    if not _the_coverage:
        _the_coverage = coverage()
    return getattr(_the_coverage, name)(*args, **kwargs)

# Define the module-level functions.
use_cache = lambda *a, **kw: _call_singleton_method('use_cache', a, kw)
start =     lambda *a, **kw: _call_singleton_method('start', a, kw)
stop =      lambda *a, **kw: _call_singleton_method('stop', a, kw)
erase =     lambda *a, **kw: _call_singleton_method('erase', a, kw)
exclude =   lambda *a, **kw: _call_singleton_method('exclude', a, kw)
analysis =  lambda *a, **kw: _call_singleton_method('analysis', a, kw)
analysis2 = lambda *a, **kw: _call_singleton_method('analysis2', a, kw)
report =    lambda *a, **kw: _call_singleton_method('report', a, kw)
annotate =  lambda *a, **kw: _call_singleton_method('annotate', a, kw)


# COPYRIGHT AND LICENSE
#
# Copyright 2001 Gareth Rees.  All rights reserved.
# Copyright 2004-2009 Ned Batchelder.  All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the
#    distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDERS AND CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
# OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
# TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.
