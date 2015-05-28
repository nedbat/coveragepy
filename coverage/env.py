"""Determine facts about the environment."""

import os
import sys

# Operating systems.
WINDOWS = sys.platform == "win32"
LINUX = sys.platform == "linux2"

# Python implementations.
PYPY = '__pypy__' in sys.builtin_module_names

# Python versions.
PYVERSION = sys.version_info
PY2 = PYVERSION < (3, 0)
PY3 = PYVERSION >= (3, 0)

# Coverage.py specifics.

# Are we using the C-implemented trace function?
C_TRACER = os.getenv('COVERAGE_TEST_TRACER', 'c') == 'c'

# Are we coverage-measuring ourselves?
METACOV = os.getenv('COVERAGE_COVERAGE', '') != ''

# Are we running our test suite?
TESTING = os.getenv('COVERAGE_TESTING', '') != ''
