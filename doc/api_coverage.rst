.. Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
.. For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

.. _api_coverage:

.. :history: 20150802T174800, new file for 4.0b1

The Coverage class
------------------

.. module:: coverage

.. autoclass:: Coverage
    :members:
    :exclude-members: use_cache, sys_info
    :special-members: __init__


Starting coverage.py automatically
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This function is used to start coverage measurement automatically when Python
starts.  See :ref:`subprocess` for details.

.. autofunction:: process_startup
