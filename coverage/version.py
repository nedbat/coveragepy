# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

"""The version and URL for coverage.py"""
# This file is exec'ed in setup.py, don't import anything!

__version__ = "4.0a7"                   # see detailed history in CHANGES.txt

__url__ = "https://coverage.readthedocs.org"
if max(__version__).isalpha():
    # For pre-releases, use a version-specific URL.
    __url__ += "/en/coverage-" + __version__
