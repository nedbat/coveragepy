.. Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
.. For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

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

There are a few different ways to use coverage.py programmatically.

The API to coverage.py is in a module called `coverage`.
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

Coverage.py supports plugins that can change its behavior, to collect
information from non-Python files, or to perform complex configuration.  See
:ref:`api_plugin` for details.

If you want to access the data that coverage.py has collected, the
:class:`coverage.CoverageData` class provides an API to read coverage.py data
files.

For more intensive data use, you might want to access the coverage.py database
file directly.  The schema is subject to change, so this is for advanced uses
only.  :ref:`dbschema` explains more.

.. toctree::
    :maxdepth: 1

    api_coverage
    api_module
    api_plugin
    api_coveragedata
    dbschema
