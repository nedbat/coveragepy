.. Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
.. For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

.. _subprocess:

======================
Measuring subprocesses
======================

If your system under test spawns subprocesses, you'll have to take extra steps
to measure coverage in those processes.  There are a few ways to ensure they
get measured.  The approach you use depends on how you create the processes.

No matter how your subprocesses are created, you will need the :ref:`parallel
option <config_run_parallel>` to collect separate data for each process, and
the :ref:`coverage combine <cmd_combine>` command to combine them together
before reporting.

To successfully write a coverage data file, the Python subprocess under
measurement must shut down cleanly and have a chance for coverage.py to run its
termination code.  It will do that when the process ends naturally, or when a
SIGTERM signal is received.

If your processes are ending with SIGTERM, you must enable the
:ref:`config_run_sigterm` setting to configure coverage to catch SIGTERM
signals and write its data.

Other ways of ending a process, like SIGKILL or :func:`os._exit
<python:os._exit>`, will prevent coverage.py from writing its data file,
leaving you with incomplete or non-existent coverage data.

.. note::

    Subprocesses will only see coverage options in the configuration file.
    Options set on the command line will not be visible to subprocesses.


Using multiprocessing
---------------------

The :mod:`multiprocessing <python:multiprocessing>` module in the Python
standard library provides high-level tools for managing subprocesses.  If you
use it, the :ref:`concurrency=multiprocessing <config_run_concurrency>` and
:ref:`sigterm <config_run_sigterm>` settings will configure coverage to measure
the subprocesses.

Even with multiprocessing, you have to be careful that all subprocesses
terminate cleanly or they won't record their coverage measurements.  For
example, the correct way to use a Pool requires closing and joining the pool
before terminating::

    with multiprocessing.Pool() as pool:
        # ... use any of the pool methods ...
        pool.close()
        pool.join()


Implicit coverage
-----------------

If you are starting subprocesses another way, you can configure Python to start
coverage when it runs.  Coverage.py includes a function designed to be invoked
when Python starts: :func:`coverage.process_startup`.  It examines the
``COVERAGE_PROCESS_START`` environment variable, and if it is set, begins
coverage measurement. The environment variable's value will be used as the name
of the :ref:`configuration file <config>` to use.

To arrange all this, you have to do two things: set a value for the
``COVERAGE_PROCESS_START`` environment variable, and then configure Python to
invoke :func:`coverage.process_startup` when Python processes start.

How you set ``COVERAGE_PROCESS_START`` depends on the details of how you create
subprocesses.  As long as the environment variable is visible in your
subprocess, it will work.

You can configure your Python installation to invoke the ``process_startup``
function in two ways:

#. Create or append to sitecustomize.py to add these lines::

    import coverage
    coverage.process_startup()

#. Create a .pth file in your Python installation containing::

    import coverage; coverage.process_startup()

The sitecustomize.py technique is cleaner, but may involve modifying an
existing sitecustomize.py, since there can be only one.  If there is no
sitecustomize.py already, you can create it in any directory on the Python
path.

The .pth technique seems like a hack, but works, and is documented behavior.
On the plus side, you can create the file with any name you like so you don't
have to coordinate with other .pth files.  On the minus side, you have to
create the file in a system-defined directory, so you may need privileges to
write it.

Note that if you use one of these techniques, you must undo them if you
uninstall coverage.py, since you will be trying to import it during Python
start-up.  Be sure to remove the change when you uninstall coverage.py, or use
a more defensive approach to importing it.


Explicit coverage
-----------------

Another option for running coverage on your subprocesses it to run coverage
explicitly as the command for your subprocess instead of using "python" as the
command.  This isn't recommended, since it requires running different code
when running coverage than when not, which can complicate your test
environment.
