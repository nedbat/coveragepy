# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

"""The version and URL for coverage.py"""
# This file is exec'ed in setup.py, don't import anything!

_maj = 4
_min = 0
_mic = 0
_rel = 0xf
_ser = 2

hexversion = (_maj << 24) + (_min << 16) + (_mic << 8) + (_rel << 4) + _ser

__version__ = "%d.%d" % (_maj, _min)
if _mic:
    __version__ += ".%d" % (_mic,)
if _rel != 0xf:
    __version__ += "%x%d" % (_rel, _ser)

__url__ = "https://coverage.readthedocs.org"
if _rel != 0xf:
    # For pre-releases, use a version-specific URL.
    __url__ += "/en/coverage-" + __version__
