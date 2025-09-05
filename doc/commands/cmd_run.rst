.. Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
.. For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

.. This file is processed with cog to insert the latest command help into the
    docs. If it's out of date, the quality checks will fail.  Running "make
    prebuild" will bring it up to date.

.. [[[cog
    from cog_helpers import show_help
.. ]]]
.. [[[end]]] (sum: 1B2M2Y8Asg)


.. _cmd_run:

Execution: ``coverage run``
---------------------------

You collect execution data by running your Python program with the **run**
command::

    $ coverage run my_program.py arg1 arg2
    blah blah ..your program's output.. blah blah

Your program runs just as if it had been invoked with the Python command line.
Arguments after your file name are passed to your program as usual in
``sys.argv``.  Rather than providing a file name, you can use the ``-m`` switch
and specify an importable module name instead, just as you can with the
Python ``-m`` switch::

    $ coverage run -m packagename.modulename arg1 arg2
    blah blah ..your program's output.. blah blah

.. note::

    In most cases, the program to use here is a test runner, not your program
    you are trying to measure. The test runner will run your tests and coverage
    will measure the coverage of your code along the way.

There are many options:

.. [[[cog show_help("run") ]]]
.. code::

    $ coverage run --help
    Usage: coverage run [options] <pyfile> [program options]

    Run a Python program, measuring code execution.

    Options:
      -a, --append          Append data to the data file. Otherwise it starts
                            clean each time.
      --branch              Measure branch coverage in addition to statement
                            coverage.
      --concurrency=LIBS    Properly measure code using a concurrency library.
                            Valid values are: eventlet, gevent, greenlet,
                            multiprocessing, thread, or a comma-list of them.
      --context=LABEL       The context label to record for this coverage run.
      --data-file=OUTFILE   Write the recorded coverage data to this file.
                            Defaults to '.coverage'. [env: COVERAGE_FILE]
      --include=PAT1,PAT2,...
                            Include only files whose paths match one of these
                            patterns. Accepts shell-style wildcards, which must be
                            quoted.
      -m, --module          <pyfile> is an importable Python module, not a script
                            path, to be run as 'python -m' would run it.
      --omit=PAT1,PAT2,...  Omit files whose paths match one of these patterns.
                            Accepts shell-style wildcards, which must be quoted.
      -L, --pylib           Measure coverage even inside the Python installed
                            library, which isn't done by default.
      -p, --parallel-mode   Append a unique suffix to the data file name to
                            collect separate data from multiple processes.
      --save-signal=SIGNAL  Specify a signal that will trigger coverage to write
                            its collected data. Supported values are: USR1, USR2.
                            Not available on Windows.
      --source=SRC1,SRC2,...
                            A list of directories or importable names of code to
                            measure.
      --timid               Use the slower Python trace function core.
      --debug=OPTS          Debug options, separated by commas. [env:
                            COVERAGE_DEBUG]
      -h, --help            Get help on this command.
      --rcfile=RCFILE       Specify configuration file. By default '.coveragerc',
                            'setup.cfg', 'tox.ini', and 'pyproject.toml' are
                            tried. [env: COVERAGE_RCFILE]
.. [[[end]]] (sum: YwMI03MDmQ)

Many of these options can also be set in the :ref:`config_run` section of your
configuration file.  Remember to put options for run after "run", but before
the program invocation::

    $ coverage run --source=dir1,dir2 my_program.py arg1 arg2
    $ coverage run --source=dir1,dir2 -m packagename.modulename arg1 arg2

If you want :ref:`branch coverage <branch>` measurement, use the ``--branch``
flag.  Otherwise only statement coverage is measured.

You can specify the code to measure with the ``--source``, ``--include``, and
``--omit`` switches.  See :ref:`Specifying source files <source_execution>` for
details of their interpretation.

.. note::

    Specifying ``--source`` on the ``coverage run`` command line won't affect
    subsequent reporting commands like ``coverage xml``.  Use the :ref:`source
    <config_run_source>` setting in the configuration file to apply the setting
    uniformly to all commands.

Coverage.py can measure multi-threaded programs by default. If you are using
more other concurrency support, with the `multiprocessing`_, `greenlet`_,
`eventlet`_, or `gevent`_ libraries, then coverage.py can get confused. Use the
``--concurrency`` switch to properly measure programs using these libraries.
Give it a value of ``multiprocessing``, ``thread``, ``greenlet``, ``eventlet``,
or ``gevent``.  Values other than ``thread`` require the :ref:`C extension
<install_extension>`.

You can combine multiple values for ``--concurrency``, separated with commas.
You can specify ``thread`` and also one of ``eventlet``, ``gevent``, or
``greenlet``.

If you are using ``--concurrency=multiprocessing``, you must set your other
options in the configuration file.  Options on the command line will not be
passed to the processes that multiprocessing creates.  Best practice is to use
the configuration file for all options.

.. _multiprocessing: https://docs.python.org/3/library/multiprocessing.html
.. _greenlet: https://greenlet.readthedocs.io/
.. _gevent: https://www.gevent.org/
.. _eventlet: https://eventlet.readthedocs.io/

If you are measuring coverage in a multi-process program, or across a number of
machines, you'll want the ``--parallel-mode`` switch to keep the data separate
during measurement.  See :ref:`cmd_combine` below.

You can specify a :ref:`static context <contexts>` for a coverage run with
``--context``.  This can be any label you want, and will be recorded with the
data.  See :ref:`contexts` for more information.

By default, coverage.py does not measure code installed with the Python
interpreter, for example, the standard library. If you want to measure that
code as well as your own, add the ``-L`` (or ``--pylib``) flag.

If your coverage results seem to be overlooking code that you know has been
executed, try running coverage.py again with the ``--timid`` flag.  This uses a
simpler but slower trace method, and might be needed in rare cases.

If you are specifying ``--save-signal``, please make sure that your program
doesn't intercept this signal. If it does, coverage won't receive the signal
and the data file will not be written.

.. versionadded:: 7.10 ``--save-signal``

Coverage.py sets an environment variable, ``COVERAGE_RUN`` to indicate that
your code is running under coverage measurement.  The value is not relevant,
and may change in the future.


.. _cmd_warnings:

Warnings
........

During execution, coverage.py may warn you about conditions it detects that
could affect the measurement process.  The possible warnings include:

Couldn't parse Python file XXX (couldnt-parse)
  During reporting, a file was thought to be Python, but it couldn't be parsed
  as Python.

Trace function changed, data is likely wrong: XXX (trace-changed)
  Coverage measurement depends on a Python setting called the trace function.
  Other Python code in your product might change that function, which will
  disrupt coverage.py's measurement.  This warning indicates that has happened.
  The XXX in the message is the new trace function value, which might provide
  a clue to the cause.

Module XXX has no Python source (module-not-python)
  You asked coverage.py to measure module XXX, but once it was imported, it
  turned out not to have a corresponding .py file.  Without a .py file,
  coverage.py can't report on missing lines.

Module XXX was never imported (module-not-imported)
  You asked coverage.py to measure module XXX, but it was never imported by
  your program.

No data was collected (no-data-collected)
  Coverage.py ran your program, but didn't measure any lines as executed.
  This could be because you asked to measure only modules that never ran,
  or for other reasons.

  To debug this problem, try using ``run --debug=trace`` to see the tracing
  decision made for each file.

Module XXX was previously imported, but not measured (module-not-measured)
  You asked coverage.py to measure module XXX, but it had already been imported
  when coverage started.  This meant coverage.py couldn't monitor its
  execution.

Already imported a file that will be measured: XXX (already-imported)
  File XXX had already been imported when coverage.py started measurement. Your
  setting for ``--source`` or ``--include`` indicates that you wanted to
  measure that file.  Lines will be missing from the coverage report since the
  execution during import hadn't been measured.

\-\-include is ignored because \-\-source is set (include-ignored)
  Both ``--include`` and ``--source`` were specified while running code.  Both
  are meant to focus measurement on a particular part of your source code, so
  ``--include`` is ignored in favor of ``--source``.

Conflicting dynamic contexts (dynamic-conflict)
  The ``[run] dynamic_context`` option is set in the configuration file, but
  something (probably a test runner plugin) is also calling the
  :meth:`.Coverage.switch_context` function to change the context. Only one of
  these mechanisms should be in use at a time.

Couldn't import C tracer (no-ctracer)
  The core tracer implemented in C should have been used, but couldn't be
  imported.  The reason is included in the warning message.  The Python tracer
  will be used instead.

sys.monitoring isn't available in this version, using default core (no-sysmon)
  You requested to use the sys.monitoring measurement core, but are running on
  Python 3.11 or lower where it isn't available.  A default core will be used
  instead.

sys.monitoring can't measure branches in this version, using default core (no-sysmon)
  You requested the sys.monitoring measurement core and also branch coverage.
  This isn't supported until the later alphas of Python 3.14.  A default core
  will be used instead.

sys.monitoring doesn't yet support dynamic contexts, using default core (no-sysmon)
  You requested the sys.monitoring measurement core and also dynamic contexts.
  This isn't supported by coverage.py yet.  A default core will be used
  instead.

Individual warnings can be disabled with the :ref:`disable_warnings
<config_run_disable_warnings>` configuration setting.  It is a list of the
short parenthetical nicknames in the warning messages.  For example, to silence
"No data was collected (no-data-collected)", add this to your configuration
file:

.. [[[cog
    show_configs(
        ini=r"""
            [run]
            disable_warnings = no-data-collected
            """,
        toml=r"""
            [tool.coverage.run]
            disable_warnings = ["no-data-collected"]
            """,
        )
.. ]]]

.. tabs::

    .. code-tab:: ini
        :caption: .coveragerc

        [run]
        disable_warnings = no-data-collected

    .. code-tab:: toml
        :caption: pyproject.toml

        [tool.coverage.run]
        disable_warnings = ["no-data-collected"]

    .. code-tab:: ini
        :caption: setup.cfg or tox.ini

        [coverage:run]
        disable_warnings = no-data-collected

.. [[[end]]] (sum: SJKFvPoXO2)


.. _cmd_datafile:

Data file
.........

Coverage.py collects execution data in a file called ".coverage".  If need be,
you can set a new file name with the ``COVERAGE_FILE`` environment variable.
This can include a path to another directory.

By default, each run of your program starts with an empty data set. If you need
to run your program multiple times to get complete data (for example, because
you need to supply different options), you can accumulate data across runs with
the ``--append`` flag on the **run** command.
