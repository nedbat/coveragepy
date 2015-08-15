.. Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
.. For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

.. _api:

===============
Coverage.py API
===============

.. :history: 20090524T134300, brand new docs.
.. :history: 20090613T164000, final touches for 3.0
.. :history: 20100221T151500, docs for 3.3 (on the plane back from PyCon)
.. :history: 20100725T211700, updated for 3.4.
.. :history: 20121111T235800, added a bit of clarification.
.. :history: 20140819T132600, change class name to Coverage


The API to coverage.py is very simple, contained in a module called `coverage`.
Most of the interface is in the :class:`coverage.Coverage` class.  Methods on
the Coverage object correspond roughly to operations available in the command
line interface. For example, a simple use would be::

    import coverage

    cov = coverage.Coverage()
    cov.start()

    # .. call your code ..

    cov.stop()
    cov.save()

    cov.html_report()

The :class:`coverage.CoverageData` class provides access to coverage data
stored in coverage.py data files.

.. toctree::
    :maxdepth: 1

    api_coverage
    api_coveragedata
    api_plugin
