.. _api:

============
Coverage API
============

:history: 20090524T134300, brand new docs.
:history: 20090613T164000, final touches for 3.0
:history: 20100221T151500, docs for 3.3 (on the plane back from PyCon)
:history: 20100725T211700, updated for 3.4.
:history: 20121111T235800, added a bit of clarification.


The API to coverage.py is very simple, contained in a single module called
`coverage`.  Most of the interface is in a single class, also called
`coverage`.  Methods on the coverage object correspond to operations available
in the command line interface. For example, a simple use would be::

    import coverage

    cov = coverage.coverage()
    cov.start()

    # .. call your code ..

    cov.stop()
    cov.save()

    cov.html_report()


The coverage module
-------------------

.. module:: coverage

.. autoclass:: coverage
    :members:


Starting coverage automatically
-------------------------------

This function is used to start coverage measurement automatically when Python
starts.  See :ref:`subprocess` for details.

.. autofunction:: process_startup
