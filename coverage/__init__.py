"""Code coverage measurement for Python.

Ned Batchelder
http://nedbatchelder.com/code/modules/coverage.html

"""

__version__ = "3.0b2"    # see detailed history in CHANGES

import sys

from coverage.control import coverage
from coverage.data import CoverageData
from coverage.cmdline import main, CoverageScript
from coverage.misc import CoverageException


# Module-level functions.  The original API to this module was based on
# functions defined directly in the module, with a singleton of the coverage()
# class.  This design hampered programmability.  Here we define the top-level
# functions to create the singleton when they are first called.

# Singleton object for use with module-level functions.  The singleton is
# created as needed when one of the module-level functions is called.
the_coverage = None

def call_singleton_method(name, args, kwargs):
    global the_coverage
    if not the_coverage:
        the_coverage = coverage()
    return getattr(the_coverage, name)(*args, **kwargs)

mod_funcs = """
    use_cache start stop erase begin_recursive end_recursive exclude
    analysis analysis2 report annotate annotate_file
    """

coverage_module = sys.modules[__name__]

for func_name in mod_funcs.split():
    # Have to define a function here to make a closure so the function name
    # is locked in.
    def func(name):
        return lambda *a, **kw: call_singleton_method(name, a, kw)
    setattr(coverage_module, func_name, func(func_name))


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
