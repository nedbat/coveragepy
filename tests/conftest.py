# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

"""
Pytest auto configuration.

This module is run automatically by pytest, to define and enable fixtures.
"""

import pytest
import warnings

from coverage import env


@pytest.fixture(autouse=True)
def set_warnings():
    """Enable DeprecationWarnings during all tests."""
    warnings.simplefilter("default")
    warnings.simplefilter("once", DeprecationWarning)

    # A warning to suppress:
    #   setuptools/py33compat.py:54: DeprecationWarning: The value of convert_charrefs will become
    #   True in 3.5. You are encouraged to set the value explicitly.
    #       unescape = getattr(html, 'unescape', html_parser.HTMLParser().unescape)
    warnings.filterwarnings(
        "ignore",
        category=DeprecationWarning,
        message="The value of convert_charrefs will become True in 3.5.",
        )
    if env.PYPY and env.PY3:
        warnings.filterwarnings("ignore", r".*unclosed file", category=ResourceWarning)
