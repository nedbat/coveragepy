.. _subprocess:

======================
Measuring subprocesses
======================

:history: 20100224T201800, new for 3.3.
:history: 20100725T211700, updated for 3.4.


Complex test suites may spawn subprocesses to run tests, either to run them in
parallel, or because subprocess behavior is an important part of the system
under test. Measuring coverage in those subprocesses can be tricky because you
have to modify the code spawning the process to invoke coverage.py.

There's an easier way to do it: coverage.py includes a function,
:func:`coverage.process_startup` designed to be invoked when Python starts.  It
examines the ``COVERAGE_PROCESS_START`` environment variable, and if it is set,
begins coverage measurement. The environment variable's value will be used as
the name of the :ref:`configuration file <config>` to use.

When using this technique, be sure to set the parallel option to true so that
multiple coverage.py runs will each write their data to a distinct file.


Configuring Python for subprocess coverage
------------------------------------------

To measure coverage in subprocesses, you have to do two things: set a value for
the ``COVERAGE_PROCESS_START`` environment variable, and then invoke
:func:`coverage.process_startup`.

How you set ``COVERAGE_PROCESS_START`` depends on the details of how you create
subprocesses.  As long as the environment variable is visible in your subprocess,
it will work.

You can configure your Python installation to invoke the ``process_startup``
function in two ways:

#. Create or append to sitecustomize.py to add these lines::

    import coverage
    coverage.process_startup()

#. Create a .pth file in your Python installation containing::

    import coverage; coverage.process_startup()

The sitecustomize.py technique is cleaner, but may involve modifying an existing
sitecustomize.py, since there can be only one.  If there is no sitecustomize.py
already, you can create it in any directory on the Python path.

The .pth technique seems like a hack, but works, and is documented behavior.
On the plus side, you can create the file with any name you like so you don't
have to coordinate with other .pth files.  On the minus side, you have to create
the file in a system-defined directory, so you may need privileges to write it.
