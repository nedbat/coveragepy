.. Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
.. For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

===========
Coverage.py
===========

Code coverage testing for Python.

|  |license| |versions| |status|
|  |ci-status| |win-ci-status| |docs| |codecov|
|  |kit| |format| |repos|
|  |tidelift| |saythanks|

Coverage.py measures code coverage, typically during test execution. It uses
the code analysis tools and tracing hooks provided in the Python standard
library to determine which lines are executable, and which have been executed.

.. |tideliftlogo| image:: https://nedbatchelder.com/pix/Tidelift_Logos_RGB_Tidelift_Shorthand_On-White_small.png
   :width: 75
   :alt: Tidelift

.. list-table::
   :widths: 10 100

   * - |tideliftlogo|
     - Professional support for coverage.py is available as part of the `Tidelift
       Subscription`_.  Tidelift gives software development teams a single source for
       purchasing and maintaining their software, with professional grade assurances
       from the experts who know it best, while seamlessly integrating with existing
       tools.

.. _Tidelift Subscription: https://tidelift.com/subscription/pkg/pypi-coverage?utm_source=pypi-coverage&utm_medium=referral&utm_campaign=readme

Coverage.py runs on many versions of Python:

* CPython 2.7.
* CPython 3.5 through alpha 3.8.
* PyPy2 7.0 and PyPy3 7.0.
* Jython 2.7.1, though not for reporting.
* IronPython 2.7.7, though not for reporting.

Documentation is on `Read the Docs`_.  Code repository and issue tracker are on
`GitHub`_.

.. _Read the Docs: https://coverage.readthedocs.io/
.. _GitHub: https://github.com/nedbat/coveragepy


**New in 5.0:** SQLite data storage, contexts, dropped support for Python 2.6
and 3.3.


Getting Started
---------------

See the `Quick Start section`_ of the docs.

.. _Quick Start section: https://coverage.readthedocs.io/#quick-start


Contributing
------------

See the `Contributing section`_ of the docs.

.. _Contributing section: https://coverage.readthedocs.io/en/latest/contributing.html


License
-------

Licensed under the `Apache 2.0 License`_.  For details, see `NOTICE.txt`_.

.. _Apache 2.0 License: http://www.apache.org/licenses/LICENSE-2.0
.. _NOTICE.txt: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt


.. |ci-status| image:: https://travis-ci.com/nedbat/coveragepy.svg?branch=master
    :target: https://travis-ci.com/nedbat/coveragepy
    :alt: Build status
.. |win-ci-status| image:: https://ci.appveyor.com/api/projects/status/kmeqpdje7h9r6vsf/branch/master?svg=true
    :target: https://ci.appveyor.com/project/nedbat/coveragepy
    :alt: Windows build status
.. |docs| image:: https://readthedocs.org/projects/coverage/badge/?version=latest&style=flat
    :target: https://coverage.readthedocs.io/
    :alt: Documentation
.. |reqs| image:: https://requires.io/github/nedbat/coveragepy/requirements.svg?branch=master
    :target: https://requires.io/github/nedbat/coveragepy/requirements/?branch=master
    :alt: Requirements status
.. |kit| image:: https://badge.fury.io/py/coverage.svg
    :target: https://pypi.org/project/coverage/
    :alt: PyPI status
.. |format| image:: https://img.shields.io/pypi/format/coverage.svg
    :target: https://pypi.org/project/coverage/
    :alt: Kit format
.. |downloads| image:: https://img.shields.io/pypi/dw/coverage.svg
    :target: https://pypi.org/project/coverage/
    :alt: Weekly PyPI downloads
.. |versions| image:: https://img.shields.io/pypi/pyversions/coverage.svg
    :target: https://pypi.org/project/coverage/
    :alt: Python versions supported
.. |status| image:: https://img.shields.io/pypi/status/coverage.svg
    :target: https://pypi.org/project/coverage/
    :alt: Package stability
.. |license| image:: https://img.shields.io/pypi/l/coverage.svg
    :target: https://pypi.org/project/coverage/
    :alt: License
.. |codecov| image:: https://codecov.io/github/nedbat/coveragepy/coverage.svg?branch=master&precision=2
    :target: https://codecov.io/github/nedbat/coveragepy?branch=master
    :alt: Coverage!
.. |repos| image:: https://repology.org/badge/tiny-repos/python:coverage.svg
    :target: https://repology.org/metapackage/python:coverage/versions
    :alt: Packaging status
.. |saythanks| image:: https://img.shields.io/badge/saythanks.io-%E2%98%BC-1EAEDB.svg
    :target: https://saythanks.io/to/nedbat
    :alt: Say thanks :)
.. |tidelift| image:: https://tidelift.com/badges/github/nedbat/coveragepy
    :target: https://tidelift.com/subscription/pkg/pypi-coverage?utm_source=pypi-coverage&utm_medium=referral&utm_campaign=readme
    :alt: Tidelift
