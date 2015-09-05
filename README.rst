===========
Coverage.py
===========

Code coverage testing for Python.

|ci-status| |win-ci-status| |reqs|

|kit| |downloads| |docs| 

Coverage.py measures code coverage, typically during test execution. It uses
the code analysis tools and tracing hooks provided in the Python standard
library to determine which lines are executable, and which have been executed.

Coverage.py runs on CPython 2.6, 2.7, 3.3, 3.4 or 3.5, PyPy 2.6, and PyPy3 2.4.

Documentation is on `Read the Docs <http://coverage.readthedocs.org>`_.
Code repository and issue tracker are on `Bitbucket <http://bitbucket.org/ned/coveragepy>`_,
with a mirrored repository on `GitHub <https://github.com/nedbat/coveragepy>`_.

**New in 4.0:** ``--concurrency``, plugins for non-Python files, setup.cfg
support, --skip-covered, HTML filtering, and more than 50 issues closed.


Quick Start
-----------

See the `quick start <http://coverage.readthedocs.org/#quick-start>`_
section of the docs.


License
-------

Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0.
For details, see https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt.


.. |ci-status| image:: https://travis-ci.org/nedbat/coveragepy.svg?branch=master
    :target: https://travis-ci.org/nedbat/coveragepy
    :alt: Build status
.. |win-ci-status| image:: https://ci.appveyor.com/api/projects/status/bitbucket/ned/coveragepy?svg=true
    :target: https://ci.appveyor.com/project/nedbat/coveragepy
    :alt: Windows build status
.. |docs| image:: https://readthedocs.org/projects/coverage/badge/?version=latest&style=flat
    :target: http://coverage.readthedocs.org
    :alt: Documentation
.. |reqs| image:: https://requires.io/github/nedbat/coveragepy/requirements.svg?branch=master
    :target: https://requires.io/github/nedbat/coveragepy/requirements/?branch=master
    :alt: Requirements status
.. |kit| image:: https://badge.fury.io/py/coverage.svg
    :target: https://pypi.python.org/pypi/coverage
    :alt: PyPI status
.. |downloads| image:: https://img.shields.io/pypi/dm/coverage.svg
    :target: https://pypi.python.org/pypi/coverage
    :alt: Monthly PyPI downloads
