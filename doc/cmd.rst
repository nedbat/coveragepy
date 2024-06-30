.. Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
.. For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

.. This file is processed with cog to insert the latest command
   help into the docs. If it's out of date, the quality checks will fail.
   Running "make prebuild" will bring it up to date.

.. [[[cog
    from cog_helpers import show_configs, show_help
.. ]]]
.. [[[end]]] (checksum: d41d8cd98f00b204e9800998ecf8427e)

.. _cmd:

==================
Command line usage
==================

.. highlight:: console

When you install coverage.py, a command-line script called ``coverage`` is
placed on your path.  To help with multi-version installs, it will also create
a ``coverage3`` alias, and a ``coverage-X.Y`` alias, depending on the version
of Python you're using.  For example, when installing on Python 3.10, you will
be able to use ``coverage``, ``coverage3``, or ``coverage-3.10`` on the command
line.

Coverage.py has a number of commands:

* **run** -- :ref:`Run a Python program and collect execution data <cmd_run>`.

* **combine** -- :ref:`Combine together a number of data files <cmd_combine>`.

* **erase** -- :ref:`Erase previously collected coverage data <cmd_erase>`.

* **report** -- :ref:`Report coverage results <cmd_report>`.

* **html** --
  :ref:`Produce annotated HTML listings with coverage results <cmd_html>`.

* **xml** -- :ref:`Produce an XML report with coverage results <cmd_xml>`.

* **json** -- :ref:`Produce a JSON report with coverage results <cmd_json>`.

* **lcov** -- :ref:`Produce an LCOV report with coverage results <cmd_lcov>`.

* **annotate** --
  :ref:`Annotate source files with coverage results <cmd_annotate>`.

* **debug** -- :ref:`Get diagnostic information <cmd_debug>`.

Help is available with the **help** command, or with the ``--help`` switch on
any other command::

    $ coverage help
    $ coverage help run
    $ coverage run --help

Version information for coverage.py can be displayed with
``coverage --version``:

.. parsed-literal::

    $ coverage --version
    Coverage.py, version |release| with C extension
    Documentation at |doc-url|

Any command can use a configuration file by specifying it with the
``--rcfile=FILE`` command-line switch.  Any option you can set on the command
line can also be set in the configuration file.  This can be a better way to
control coverage.py since the configuration file can be checked into source
control, and can provide options that other invocation techniques (like test
runner plugins) may not offer. See :ref:`config` for more details.


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
      -a, --append          Append coverage data to .coverage, otherwise it starts
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
      -p, --parallel-mode   Append the machine name, process id and random number
                            to the data file name to simplify collecting data from
                            many processes.
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
.. [[[end]]] (checksum: b1a0fffe2768fc142f1d97ae556b621d)

If you want :ref:`branch coverage <branch>` measurement, use the ``--branch``
flag.  Otherwise only statement coverage is measured.

You can specify the code to measure with the ``--source``, ``--include``, and
``--omit`` switches.  See :ref:`Specifying source files <source_execution>` for
details of their interpretation.  Remember to put options for run after "run",
but before the program invocation::

    $ coverage run --source=dir1,dir2 my_program.py arg1 arg2
    $ coverage run --source=dir1,dir2 -m packagename.modulename arg1 arg2

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

If you are using ``--concurrency=multiprocessing``, you must set other options
in the configuration file.  Options on the command line will not be passed to
the processes that multiprocessing creates.  Best practice is to use the
configuration file for all options.

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

In Python 3.12 and above, you can try an experimental core based on the new
:mod:`sys.monitoring <python:sys.monitoring>` module by defining a
``COVERAGE_CORE=sysmon`` environment variable.  This should be faster, though
plugins and dynamic contexts are not yet supported with it.

Coverage.py sets an environment variable, ``COVERAGE_RUN`` to indicate that
your code is running under coverage measurement.  The value is not relevant,
and may change in the future.

These options can also be set in the :ref:`config_run` section of your
.coveragerc file.


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

sys.monitoring isn't available, using default core (no-sysmon)
  You requested to use the sys.monitoring measurement core, but are running on
  Python 3.11 or lower where it isn't available.  A default core will be used
  instead.

Individual warnings can be disabled with the :ref:`disable_warnings
<config_run_disable_warnings>` configuration setting.  To silence "No data was
collected," add this to your configuration file:

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

.. [[[end]]] (checksum: 489285bcfa173b69a286f03fe13e4554)


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


.. _cmd_combine:

Combining data files: ``coverage combine``
------------------------------------------

Often test suites are run under different conditions, for example, with
different versions of Python, or dependencies, or on different operating
systems.  In these cases, you can collect coverage data for each test run, and
then combine all the separate data files into one combined file for reporting.

The **combine** command reads a number of separate data files, matches the data
by source file name, and writes a combined data file with all of the data.

Coverage normally writes data to a filed named ".coverage".  The ``run
--parallel-mode`` switch (or ``[run] parallel=True`` configuration option)
tells coverage to expand the file name to include machine name, process id, and
a random number so that every data file is distinct::

    .coverage.Neds-MacBook-Pro.local.88335.316857
    .coverage.Geometer.8044.799674

You can also define a new data file name with the ``[run] data_file`` option.

Once you have created a number of these files, you can copy them all to a
single directory, and use the **combine** command to combine them into one
.coverage data file::

    $ coverage combine

You can also name directories or files to be combined on the command line::

    $ coverage combine data1.dat windows_data_files/

Coverage.py will collect the data from those places and combine them.  The
current directory isn't searched if you use command-line arguments.  If you
also want data from the current directory, name it explicitly on the command
line.

When coverage.py combines data files, it looks for files named the same as the
data file (defaulting to ".coverage"), with a dotted suffix.  Here are some
examples of data files that can be combined::

    .coverage.machine1
    .coverage.20120807T212300
    .coverage.last_good_run.ok

An existing combined data file is ignored and re-written. If you want to use
**combine** to accumulate results into the .coverage data file over a number of
runs, use the ``--append`` switch on the **combine** command.  This behavior
was the default before version 4.2.

If any of the data files can't be read, coverage.py will print a warning
indicating the file and the problem.

The original input data files are deleted once they've been combined. If you
want to keep those files, use the ``--keep`` command-line option.

.. [[[cog show_help("combine") ]]]
.. code::

    $ coverage combine --help
    Usage: coverage combine [options] <path1> <path2> ... <pathN>

    Combine data from multiple coverage files. The combined results are written to
    a single file representing the union of the data. The positional arguments are
    data files or directories containing data files. If no paths are provided,
    data files in the default data file's directory are combined.

    Options:
      -a, --append          Append coverage data to .coverage, otherwise it starts
                            clean each time.
      --data-file=DATAFILE  Base name of the data files to operate on. Defaults to
                            '.coverage'. [env: COVERAGE_FILE]
      --keep                Keep original coverage files, otherwise they are
                            deleted.
      -q, --quiet           Don't print messages about what is happening.
      --debug=OPTS          Debug options, separated by commas. [env:
                            COVERAGE_DEBUG]
      -h, --help            Get help on this command.
      --rcfile=RCFILE       Specify configuration file. By default '.coveragerc',
                            'setup.cfg', 'tox.ini', and 'pyproject.toml' are
                            tried. [env: COVERAGE_RCFILE]
.. [[[end]]] (checksum: 0bdd83f647ee76363c955bedd9ddf749)


.. _cmd_combine_remapping:

Re-mapping paths
................

To combine data for a source file, coverage has to find its data in each of the
data files.  Different test runs may run the same source file from different
locations. For example, different operating systems will use different paths
for the same file, or perhaps each Python version is run from a different
subdirectory.  Coverage needs to know that different file paths are actually
the same source file for reporting purposes.

You can tell coverage.py how different source locations relate with a
``[paths]`` section in your configuration file (see :ref:`config_paths`).
It might be more convenient to use the ``[run] relative_files``
setting to store relative file paths (see :ref:`relative_files
<config_run_relative_files>`).

If data isn't combining properly, you can see details about the inner workings
with ``--debug=pathmap``.


.. _cmd_erase:

Erase data: ``coverage erase``
------------------------------

To erase the collected data, use the **erase** command:

.. [[[cog show_help("erase") ]]]
.. code::

    $ coverage erase --help
    Usage: coverage erase [options]

    Erase previously collected coverage data.

    Options:
      --data-file=DATAFILE  Base name of the data files to operate on. Defaults to
                            '.coverage'. [env: COVERAGE_FILE]
      --debug=OPTS          Debug options, separated by commas. [env:
                            COVERAGE_DEBUG]
      -h, --help            Get help on this command.
      --rcfile=RCFILE       Specify configuration file. By default '.coveragerc',
                            'setup.cfg', 'tox.ini', and 'pyproject.toml' are
                            tried. [env: COVERAGE_RCFILE]
.. [[[end]]] (checksum: cfeaef66ce8d5154dc6914831030b46b)

If your configuration file indicates parallel data collection, **erase** will
remove all of the data files.


.. _cmd_reporting:

Reporting
---------

Coverage.py provides a few styles of reporting, with the **report**, **html**,
**annotate**, **json**, **lcov**, and **xml** commands.  They share a number
of common options.

The command-line arguments are module or file names to report on, if you'd like
to report on a subset of the data collected.

The ``--include`` and ``--omit`` flags specify lists of file name patterns.
They control which files to report on, and are described in more detail in
:ref:`source`.

The ``-i`` or ``--ignore-errors`` switch tells coverage.py to ignore problems
encountered trying to find source files to report on.  This can be useful if
some files are missing, or if your Python execution is tricky enough that file
names are synthesized without real source files.

If you provide a ``--fail-under`` value, the total percentage covered will be
compared to that value.  If it is less, the command will exit with a status
code of 2, indicating that the total coverage was less than your target.  This
can be used as part of a pass/fail condition, for example in a continuous
integration server.  This option isn't available for **annotate**.

These options can also be set in your .coveragerc file. See
:ref:`Configuration: [report] <config_report>`.


.. _cmd_report:

Coverage summary: ``coverage report``
-------------------------------------

The simplest reporting is a textual summary produced with **report**::

    $ coverage report
    Name                      Stmts   Miss  Cover
    ---------------------------------------------
    my_program.py                20      4    80%
    my_module.py                 15      2    86%
    my_other_module.py           56      6    89%
    ---------------------------------------------
    TOTAL                        91     12    87%

For each module executed, the report shows the count of executable statements,
the number of those statements missed, and the resulting coverage, expressed
as a percentage.

.. [[[cog show_help("report") ]]]
.. code::

    $ coverage report --help
    Usage: coverage report [options] [modules]

    Report coverage statistics on modules.

    Options:
      --contexts=REGEX1,REGEX2,...
                            Only display data from lines covered in the given
                            contexts. Accepts Python regexes, which must be
                            quoted.
      --data-file=INFILE    Read coverage data for report generation from this
                            file. Defaults to '.coverage'. [env: COVERAGE_FILE]
      --fail-under=MIN      Exit with a status of 2 if the total coverage is less
                            than MIN.
      --format=FORMAT       Output format, either text (default), markdown, or
                            total.
      -i, --ignore-errors   Ignore errors while reading source files.
      --include=PAT1,PAT2,...
                            Include only files whose paths match one of these
                            patterns. Accepts shell-style wildcards, which must be
                            quoted.
      --omit=PAT1,PAT2,...  Omit files whose paths match one of these patterns.
                            Accepts shell-style wildcards, which must be quoted.
      --precision=N         Number of digits after the decimal point to display
                            for reported coverage percentages.
      --sort=COLUMN         Sort the report by the named column: name, stmts,
                            miss, branch, brpart, or cover. Default is name.
      -m, --show-missing    Show line numbers of statements in each module that
                            weren't executed.
      --skip-covered        Skip files with 100% coverage.
      --no-skip-covered     Disable --skip-covered.
      --skip-empty          Skip files with no code.
      --debug=OPTS          Debug options, separated by commas. [env:
                            COVERAGE_DEBUG]
      -h, --help            Get help on this command.
      --rcfile=RCFILE       Specify configuration file. By default '.coveragerc',
                            'setup.cfg', 'tox.ini', and 'pyproject.toml' are
                            tried. [env: COVERAGE_RCFILE]
.. [[[end]]] (checksum: 167272a29d9e7eb017a592a0e0747a06)

The ``-m`` flag also shows the line numbers of missing statements::

    $ coverage report -m
    Name                      Stmts   Miss  Cover   Missing
    -------------------------------------------------------
    my_program.py                20      4    80%   33-35, 39
    my_module.py                 15      2    86%   8, 12
    my_other_module.py           56      6    89%   17-23
    -------------------------------------------------------
    TOTAL                        91     12    87%

If you are using branch coverage, then branch statistics will be reported in
the Branch and BrPart (for Partial Branch) columns, the Missing column will
detail the missed branches::

    $ coverage report -m
    Name                      Stmts   Miss Branch BrPart  Cover   Missing
    ---------------------------------------------------------------------
    my_program.py                20      4     10      2    80%   33-35, 36->38, 39
    my_module.py                 15      2      3      0    86%   8, 12
    my_other_module.py           56      6      5      1    89%   17-23, 40->45
    ---------------------------------------------------------------------
    TOTAL                        91     12     18      3    87%

You can restrict the report to only certain files by naming them on the
command line::

    $ coverage report -m my_program.py my_other_module.py
    Name                      Stmts   Miss  Cover   Missing
    -------------------------------------------------------
    my_program.py                20      4    80%   33-35, 39
    my_other_module.py           56      6    89%   17-23
    -------------------------------------------------------
    TOTAL                        76     10    87%

The ``--skip-covered`` switch will skip any file with 100% coverage, letting
you focus on the files that still need attention. The ``--no-skip-covered``
option can be used if needed to see all the files.  The ``--skip-empty`` switch
will skip any file with no executable statements.

If you have :ref:`recorded contexts <contexts>`, the ``--contexts`` option lets
you choose which contexts to report on.  See :ref:`context_reporting` for
details.

The ``--precision`` option controls the number of digits displayed after the
decimal point in coverage percentages, defaulting to none.

The ``--sort`` option is the name of a column to sort the report by.

The ``--format`` option controls the style of the report.  ``--format=text``
creates plain text tables as shown above.  ``--format=markdown`` creates
Markdown tables.  ``--format=total`` writes out a single number, the total
coverage percentage as shown at the end of the tables, but without a percent
sign.

Other common reporting options are described above in :ref:`cmd_reporting`.
These options can also be set in your .coveragerc file. See
:ref:`Configuration: [report] <config_report>`.


.. _cmd_html:

HTML reporting: ``coverage html``
---------------------------------

Coverage.py can annotate your source code to show which lines were executed
and which were not.  The **html** command creates an HTML report similar to the
**report** summary, but as an HTML file.  Each module name links to the source
file decorated to show the status of each line.

Here's a `sample report`__.

__ https://nedbatchelder.com/files/sample_coverage_html/index.html

Lines are highlighted: green for executed, red for missing, and gray for
excluded.  If you've used branch coverage, partial branches are yellow.  The
colored counts at the top of the file are buttons to turn on and off the
highlighting.

A number of keyboard shortcuts are available for navigating the report.
Click the keyboard icon in the upper right to see the complete list.

.. [[[cog show_help("html") ]]]
.. code::

    $ coverage html --help
    Usage: coverage html [options] [modules]

    Create an HTML report of the coverage of the files.  Each file gets its own
    page, with the source decorated to show executed, excluded, and missed lines.

    Options:
      --contexts=REGEX1,REGEX2,...
                            Only display data from lines covered in the given
                            contexts. Accepts Python regexes, which must be
                            quoted.
      -d DIR, --directory=DIR
                            Write the output files to DIR.
      --data-file=INFILE    Read coverage data for report generation from this
                            file. Defaults to '.coverage'. [env: COVERAGE_FILE]
      --fail-under=MIN      Exit with a status of 2 if the total coverage is less
                            than MIN.
      -i, --ignore-errors   Ignore errors while reading source files.
      --include=PAT1,PAT2,...
                            Include only files whose paths match one of these
                            patterns. Accepts shell-style wildcards, which must be
                            quoted.
      --omit=PAT1,PAT2,...  Omit files whose paths match one of these patterns.
                            Accepts shell-style wildcards, which must be quoted.
      --precision=N         Number of digits after the decimal point to display
                            for reported coverage percentages.
      -q, --quiet           Don't print messages about what is happening.
      --show-contexts       Show contexts for covered lines.
      --skip-covered        Skip files with 100% coverage.
      --no-skip-covered     Disable --skip-covered.
      --skip-empty          Skip files with no code.
      --title=TITLE         A text string to use as the title on the HTML.
      --debug=OPTS          Debug options, separated by commas. [env:
                            COVERAGE_DEBUG]
      -h, --help            Get help on this command.
      --rcfile=RCFILE       Specify configuration file. By default '.coveragerc',
                            'setup.cfg', 'tox.ini', and 'pyproject.toml' are
                            tried. [env: COVERAGE_RCFILE]
.. [[[end]]] (checksum: e3a1a6e24ad9b303ba06d42880ed0219)

The title of the report can be set with the ``title`` setting in the
``[html]`` section of the configuration file, or the ``--title`` switch on
the command line.

If you prefer a different style for your HTML report, you can provide your
own CSS file to apply, by specifying a CSS file in the ``[html]`` section of
the configuration file.  See :ref:`config_html_extra_css` for details.

The ``-d`` argument specifies an output directory, defaulting to "htmlcov"::

    $ coverage html -d coverage_html

Other common reporting options are described above in :ref:`cmd_reporting`.

Generating the HTML report can be time-consuming.  Stored with the HTML report
is a data file that is used to speed up reporting the next time.  If you
generate a new report into the same directory, coverage.py will skip
generating unchanged pages, making the process faster.

The ``--skip-covered`` switch will skip any file with 100% coverage, letting
you focus on the files that still need attention.  The ``--skip-empty`` switch
will skip any file with no executable statements.

The ``--precision`` option controls the number of digits displayed after the
decimal point in coverage percentages, defaulting to none.

If you have :ref:`recorded contexts <contexts>`, the ``--contexts`` option lets
you choose which contexts to report on, and the ``--show-contexts`` option will
annotate lines with the contexts that ran them.  See :ref:`context_reporting`
for details.

These options can also be set in your .coveragerc file. See
:ref:`Configuration: [html] <config_html>`.


.. _cmd_xml:

XML reporting: ``coverage xml``
-------------------------------

The **xml** command writes coverage data to a "coverage.xml" file in a format
compatible with `Cobertura`_.

.. _Cobertura: http://cobertura.github.io/cobertura/

.. [[[cog show_help("xml") ]]]
.. code::

    $ coverage xml --help
    Usage: coverage xml [options] [modules]

    Generate an XML report of coverage results.

    Options:
      --data-file=INFILE    Read coverage data for report generation from this
                            file. Defaults to '.coverage'. [env: COVERAGE_FILE]
      --fail-under=MIN      Exit with a status of 2 if the total coverage is less
                            than MIN.
      -i, --ignore-errors   Ignore errors while reading source files.
      --include=PAT1,PAT2,...
                            Include only files whose paths match one of these
                            patterns. Accepts shell-style wildcards, which must be
                            quoted.
      --omit=PAT1,PAT2,...  Omit files whose paths match one of these patterns.
                            Accepts shell-style wildcards, which must be quoted.
      -o OUTFILE            Write the XML report to this file. Defaults to
                            'coverage.xml'
      -q, --quiet           Don't print messages about what is happening.
      --skip-empty          Skip files with no code.
      --debug=OPTS          Debug options, separated by commas. [env:
                            COVERAGE_DEBUG]
      -h, --help            Get help on this command.
      --rcfile=RCFILE       Specify configuration file. By default '.coveragerc',
                            'setup.cfg', 'tox.ini', and 'pyproject.toml' are
                            tried. [env: COVERAGE_RCFILE]
.. [[[end]]] (checksum: 8b239d89534be0b2c69489e10b1352a9)

You can specify the name of the output file with the ``-o`` switch.

Other common reporting options are described above in :ref:`cmd_reporting`.

To include complete file paths in the output file, rather than just
the file name, use [include] vs [source] in your ".coveragerc" file.

For example, use this:

.. code:: ini

    [run]
    include =
        foo/*
        bar/*


which will result in

.. code:: xml

    <class filename="bar/hello.py">
    <class filename="bar/baz/hello.py">
    <class filename="foo/hello.py">

in place of this:

.. code:: ini

    [run]
    source =
        foo
        bar

which may result in

.. code:: xml

    <class filename="hello.py">
    <class filename="baz/hello.py">

These options can also be set in your .coveragerc file. See
:ref:`Configuration: [xml] <config_xml>`.


.. _cmd_json:

JSON reporting: ``coverage json``
---------------------------------

The **json** command writes coverage data to a "coverage.json" file.

.. [[[cog show_help("json") ]]]
.. code::

    $ coverage json --help
    Usage: coverage json [options] [modules]

    Generate a JSON report of coverage results.

    Options:
      --contexts=REGEX1,REGEX2,...
                            Only display data from lines covered in the given
                            contexts. Accepts Python regexes, which must be
                            quoted.
      --data-file=INFILE    Read coverage data for report generation from this
                            file. Defaults to '.coverage'. [env: COVERAGE_FILE]
      --fail-under=MIN      Exit with a status of 2 if the total coverage is less
                            than MIN.
      -i, --ignore-errors   Ignore errors while reading source files.
      --include=PAT1,PAT2,...
                            Include only files whose paths match one of these
                            patterns. Accepts shell-style wildcards, which must be
                            quoted.
      --omit=PAT1,PAT2,...  Omit files whose paths match one of these patterns.
                            Accepts shell-style wildcards, which must be quoted.
      -o OUTFILE            Write the JSON report to this file. Defaults to
                            'coverage.json'
      --pretty-print        Format the JSON for human readers.
      -q, --quiet           Don't print messages about what is happening.
      --show-contexts       Show contexts for covered lines.
      --debug=OPTS          Debug options, separated by commas. [env:
                            COVERAGE_DEBUG]
      -h, --help            Get help on this command.
      --rcfile=RCFILE       Specify configuration file. By default '.coveragerc',
                            'setup.cfg', 'tox.ini', and 'pyproject.toml' are
                            tried. [env: COVERAGE_RCFILE]
.. [[[end]]] (checksum: e53e60cb65d971c35d1db1c08324b72e)

You can specify the name of the output file with the ``-o`` switch.  The JSON
can be nicely formatted by specifying the ``--pretty-print`` switch.

Other common reporting options are described above in :ref:`cmd_reporting`.
These options can also be set in your .coveragerc file. See
:ref:`Configuration: [json] <config_json>`.


.. _cmd_lcov:

LCOV reporting: ``coverage lcov``
---------------------------------

The **lcov** command writes coverage data to a "coverage.lcov" file.

.. [[[cog show_help("lcov") ]]]
.. code::

    $ coverage lcov --help
    Usage: coverage lcov [options] [modules]

    Generate an LCOV report of coverage results.

    Options:
      --data-file=INFILE    Read coverage data for report generation from this
                            file. Defaults to '.coverage'. [env: COVERAGE_FILE]
      --fail-under=MIN      Exit with a status of 2 if the total coverage is less
                            than MIN.
      -i, --ignore-errors   Ignore errors while reading source files.
      --include=PAT1,PAT2,...
                            Include only files whose paths match one of these
                            patterns. Accepts shell-style wildcards, which must be
                            quoted.
      -o OUTFILE            Write the LCOV report to this file. Defaults to
                            'coverage.lcov'
      --omit=PAT1,PAT2,...  Omit files whose paths match one of these patterns.
                            Accepts shell-style wildcards, which must be quoted.
      -q, --quiet           Don't print messages about what is happening.
      --debug=OPTS          Debug options, separated by commas. [env:
                            COVERAGE_DEBUG]
      -h, --help            Get help on this command.
      --rcfile=RCFILE       Specify configuration file. By default '.coveragerc',
                            'setup.cfg', 'tox.ini', and 'pyproject.toml' are
                            tried. [env: COVERAGE_RCFILE]
.. [[[end]]] (checksum: 16acfbae8011d2e3b620695c5fe13746)

Common reporting options are described above in :ref:`cmd_reporting`.
Also see :ref:`Configuration: [lcov] <config_lcov>`.

.. versionadded:: 6.3


.. _cmd_annotate:

Text annotation: ``coverage annotate``
--------------------------------------

.. note::

    The **annotate** command has been obsoleted by more modern reporting tools,
    including the **html** command.

The **annotate** command produces a text annotation of your source code.  With
a ``-d`` argument specifying an output directory, each Python file becomes a
text file in that directory.  Without ``-d``, the files are written into the
same directories as the original Python files.

Coverage status for each line of source is indicated with a character prefix::

    > executed
    ! missing (not executed)
    - excluded

For example::

      # A simple function, never called with x==1

    > def h(x):
          """Silly function."""
    -     if 0:  # pragma: no cover
    -         pass
    >     if x == 1:
    !         a = 1
    >     else:
    >         a = 2

.. [[[cog show_help("annotate") ]]]
.. code::

    $ coverage annotate --help
    Usage: coverage annotate [options] [modules]

    Make annotated copies of the given files, marking statements that are executed
    with > and statements that are missed with !.

    Options:
      -d DIR, --directory=DIR
                            Write the output files to DIR.
      --data-file=INFILE    Read coverage data for report generation from this
                            file. Defaults to '.coverage'. [env: COVERAGE_FILE]
      -i, --ignore-errors   Ignore errors while reading source files.
      --include=PAT1,PAT2,...
                            Include only files whose paths match one of these
                            patterns. Accepts shell-style wildcards, which must be
                            quoted.
      --omit=PAT1,PAT2,...  Omit files whose paths match one of these patterns.
                            Accepts shell-style wildcards, which must be quoted.
      --debug=OPTS          Debug options, separated by commas. [env:
                            COVERAGE_DEBUG]
      -h, --help            Get help on this command.
      --rcfile=RCFILE       Specify configuration file. By default '.coveragerc',
                            'setup.cfg', 'tox.ini', and 'pyproject.toml' are
                            tried. [env: COVERAGE_RCFILE]
.. [[[end]]] (checksum: fd7d8fbd2dd6e24d37f868b389c2ad6d)

Other common reporting options are described above in :ref:`cmd_reporting`.


.. _cmd_debug:

Diagnostics: ``coverage debug``
-------------------------------

The **debug** command shows internal information to help diagnose problems.
If you are reporting a bug about coverage.py, including the output of this
command can often help::

    $ coverage debug sys > please_attach_to_bug_report.txt

A few types of information are available:

* ``config``: show coverage's configuration
* ``sys``: show system configuration
* ``data``: show a summary of the collected coverage data
* ``premain``: show the call stack invoking coverage
* ``pybehave``: show internal flags describing Python behavior

.. [[[cog show_help("debug") ]]]
.. code::

    $ coverage debug --help
    Usage: coverage debug <topic>

    Display information about the internals of coverage.py, for diagnosing
    problems. Topics are: 'data' to show a summary of the collected data; 'sys' to
    show installation information; 'config' to show the configuration; 'premain'
    to show what is calling coverage; 'pybehave' to show internal flags describing
    Python behavior.

    Options:
      --debug=OPTS     Debug options, separated by commas. [env: COVERAGE_DEBUG]
      -h, --help       Get help on this command.
      --rcfile=RCFILE  Specify configuration file. By default '.coveragerc',
                       'setup.cfg', 'tox.ini', and 'pyproject.toml' are tried.
                       [env: COVERAGE_RCFILE]
.. [[[end]]] (checksum: c9b8dfb644da3448830b1c99bffa6880)

.. _cmd_run_debug:

``--debug``
...........

The ``--debug`` option is also available on all commands.  It instructs
coverage.py to log internal details of its operation, to help with diagnosing
problems.  It takes a comma-separated list of options, each indicating a facet
of operation to log:

* ``callers``: annotate each debug message with a stack trace of the callers
  to that point.

* ``config``: before starting, dump all the :ref:`configuration <config>`
  values.

* ``dataio``: log when reading or writing any data file.

* ``dataop``: log a summary of data being added to CoverageData objects.

* ``dataop2``: when used with ``debug=dataop``, log the actual data being added
  to CoverageData objects.

* ``lock``: log operations acquiring locks in the data layer.

* ``multiproc``: log the start and stop of multiprocessing processes.

* ``pathmap``: log the remapping of paths that happens during ``coverage
  combine``. See :ref:`config_paths`.

* ``pid``: annotate all warnings and debug output with the process and thread
  ids.

* ``plugin``: print information about plugin operations.

* ``process``: show process creation information, and changes in the current
  directory.  This also writes a time stamp and command arguments into the data
  file.

* ``pybehave``: show the values of `internal flags <env.py_>`_ describing the
  behavior of the current version of Python.

* ``pytest``: indicate the name of the current pytest test when it changes.

* ``self``: annotate each debug message with the object printing the message.

* ``sql``: log the SQL statements used for recording data.

* ``sqldata``: when used with ``debug=sql``, also log the full data being used
  in SQL statements.

* ``sys``: before starting, dump all the system and environment information,
  as with :ref:`coverage debug sys <cmd_debug>`.

* ``trace``: print every decision about whether to trace a file or not. For
  files not being traced, the reason is also given.

.. _env.py: https://github.com/nedbat/coveragepy/blob/master/coverage/env.py

Debug options can also be set with the ``COVERAGE_DEBUG`` environment variable,
a comma-separated list of these options, or in the :ref:`config_run_debug`
section of the .coveragerc file.

The debug output goes to stderr, unless the :ref:`config_run_debug_file`
setting or the ``COVERAGE_DEBUG_FILE`` environment variable names a different
file, which will be appended to.  This can be useful because many test runners
capture output, which could hide important details.  ``COVERAGE_DEBUG_FILE``
accepts the special names ``stdout`` and ``stderr`` to write to those
destinations.
