# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Code coverage measurement for Python.

Ned Batchelder
https://nedbatchelder.com/code/coverage

"""

import sys

from coverage.version import __version__ as __version__, __url__ as __url__, version_info as version_info

from coverage.control import Coverage as Coverage, process_startup as process_startup
from coverage.data import CoverageData as CoverageData
from coverage.exceptions import CoverageException as CoverageException
from coverage.plugin import CoveragePlugin as CoveragePlugin, FileTracer as FileTracer, FileReporter as FileReporter
from coverage.pytracer import PyTracer as PyTracer

# Backward compatibility.
coverage = Coverage

# On Windows, we encode and decode deep enough that something goes wrong and
# the encodings.utf_8 module is loaded and then unloaded, I don't know why.
# Adding a reference here prevents it from being unloaded.  Yuk.
import encodings.utf_8      # pylint: disable=wrong-import-position, wrong-import-order

# Because of the "from coverage.control import fooey" lines at the top of the
# file, there's an entry for coverage.coverage in sys.modules, mapped to None.
# This makes some inspection tools (like pydoc) unable to find the class
# coverage.coverage.  So remove that entry.
try:
    del sys.modules['coverage.coverage']
except KeyError:
    pass
