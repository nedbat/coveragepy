.. Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
.. For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

.. _contexts:

====================
Measurement Contexts
====================

.. :history: 20180921T085400, new for 5.0

.. versionadded:: 5.0

Coverage.py measures whether code was run, but it can also record the context
in which it was run.  This can provide more information to help you understand
the behavior of your tests.

There are two kinds of context: static and dynamic.  Static contexts are fixed
for an entire run, and are set explicitly with an option.  Dynamic contexts
change over the course of a single run.


Static contexts
---------------

A static context is set by an option when you run coverage.py.  The value is
fixed for the duration of a run.  They can be any text you like, for example,
"python3" or "with_numpy".  The context is recorded with the data.

When you :ref:`combine multiple data files <cmd_combining>` together, they can
have differing contexts.  All of the information is retained, so that the
different contexts are correctly recorded in the combined file.

A static context is specified with the ``--context=CONTEXT`` option to
:ref:`coverage run <cmd_run>`.


Dynamic contexts
----------------

Dynamic contexts are found during execution.  There is currently support for
one kind: test function names.  Set the ``dynamic_context`` option to
``test_function`` in the configuration file::

    [run]
    dynamic_context = test_function

Each test function you run will be considered a separate dynamic context, and
coverage data will be segregated for each.  A test function is any function
whose names starts with "test".

Ideas are welcome for other dynamic contexts that would be useful.


Context reporting
-----------------

There is currently no support for using contexts during reporting.  I'm
interested to `hear your ideas`__ for what would be useful.

__  https://nedbatchelder.com/site/aboutned.html
