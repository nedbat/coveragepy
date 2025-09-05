.. Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
.. For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

.. This file is processed with cog to insert the latest command help into the
    docs. If it's out of date, the quality checks will fail.  Running "make
    prebuild" will bring it up to date.

.. [[[cog
    from cog_helpers import show_configs
.. ]]]
.. [[[end]]] (sum: 1B2M2Y8Asg)

.. _messages:

========
Messages
========

Coverage.py has a number of messages for conditions that could affect
measurement or reporting.


.. _cmd_warnings:
.. _warnings:

Warnings
........

Warnings are issued for possible problems but don't stop the measurement or
reporting.  See below for the details of each warning, and how to suppress
warnings you don't need to see.

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
