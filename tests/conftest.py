# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

"""
Pytest auto configuration.

This module is run automatically by pytest, to define and enable fixtures.
"""

import pytest
import warnings


@pytest.fixture(autouse=True)
def set_warnings():
    """Enable DeprecationWarnings during all tests."""
    warnings.simplefilter("default")
    warnings.simplefilter("once", DeprecationWarning)
