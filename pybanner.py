# For printing the python version during tests.

import platform
import sys

try:
    impl = platform.python_implementation()
except AttributeError:
    impl = "Python"

version = platform.python_version()

if '__pypy__' in sys.builtin_module_names:
    version += " (pypy %s)" % ".".join([str(v) for v in sys.pypy_version_info])

print('=== %s %s %s (%s) ===' % (impl, version, sys.argv[1], sys.executable))
