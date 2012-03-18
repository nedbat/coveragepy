# For printing the python version during tests.

import platform
import sys

try:
    impl = platform.python_implementation()
except AttributeError:
    impl = "Python"

print('=== %s %s %s (%s) ===' % (impl, platform.python_version(), sys.argv[1], sys.executable))
