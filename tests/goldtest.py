# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""A test base class for tests based on gold file comparison."""

import os

from unittest_mixins import change_dir    # pylint: disable=unused-import

from tests.coveragetest import TESTS_DIR
# Import helpers, eventually test_farm.py will go away.
from tests.test_farm import (       # pylint: disable=unused-import
    compare, contains, doesnt_contain, contains_any,
)

def gold_path(path):
    """Get a path to a gold file for comparison."""
    return os.path.join(TESTS_DIR, "farm", path)
