"""Code coverage measurement for Python.

Ned Batchelder
http://nedbatchelder.com/code/coverage

"""

from coverage.version import __version__, __url__

from coverage.control import Coverage, process_startup
from coverage.data import CoverageData
from coverage.cmdline import main, CoverageScript
from coverage.misc import CoverageException
from coverage.plugin import CoveragePlugin

# Backward compatibility.
coverage = Coverage

# On Windows, we encode and decode deep enough that something goes wrong and
# the encodings.utf_8 module is loaded and then unloaded, I don't know why.
# Adding a reference here prevents it from being unloaded.  Yuk.
import encodings.utf_8

# Because of the "from coverage.control import fooey" lines at the top of the
# file, there's an entry for coverage.coverage in sys.modules, mapped to None.
# This makes some inspection tools (like pydoc) unable to find the class
# coverage.coverage.  So remove that entry.
import sys
try:
    del sys.modules['coverage.coverage']
except KeyError:
    pass


# COPYRIGHT AND LICENSE
#
# Copyright 2001 Gareth Rees.  All rights reserved.
# Copyright 2004-2015 Ned Batchelder.  All rights reserved.
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
