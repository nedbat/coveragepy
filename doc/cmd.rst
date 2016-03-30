.. Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
.. For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

.. _cmd:

==============================
Coverage.py command line usage
==============================

.. :history: 20090524T134300, brand new docs.
.. :history: 20090613T164000, final touches for 3.0
.. :history: 20090913T084400, new command line syntax
.. :history: 20091004T170700, changes for 3.1
.. :history: 20091127T200700, changes for 3.2
.. :history: 20100223T200600, changes for 3.3
.. :history: 20100725T211700, updated for 3.4
.. :history: 20110827T212500, updated for 3.5.1, combining aliases
.. :history: 20120119T075600, Added some clarification from George Paci
.. :history: 20120504T091800, Added info about execution warnings, and 3.5.2 stuff.
.. :history: 20120807T211600, Clarified the combine rules.
.. :history: 20121003T074600, Fixed an option reference, https://bitbucket.org/ned/coveragepy/issue/200/documentation-mentions-output-xml-instead
.. :history: 20121117T091000, Added command aliases.
.. :history: 20140924T193000, Added --concurrency
.. :history: 20150802T174700, Updated for 4.0b1

.. highlight:: console


When you install coverage.py, a command-line script simply called ``coverage``
is placed in your Python scripts directory.  To help with multi-version
installs, it will also create either a ``coverage2`` or ``coverage3`` alias,
and a ``coverage-X.Y`` alias, depending on the version of Python you're using.
For example, when installing on Python 2.7, you will be able to use
``coverage``, ``coverage2``, or ``coverage-2.7`` on the command line.

Coverage.py has a number of commands which determine the action performed:

* **run** -- Run a Python program and collect execution data.

* **report** -- Report coverage results.

* **html** -- Produce annotated HTML listings with coverage results.

* **xml** -- Produce an XML report with coverage results.

* **annotate** -- Annotate source files with coverage results.

* **erase** -- Erase previously collected coverage data.

* **combine** -- Combine together a number of data files.

* **debug** -- Get diagnostic information.

Help is available with the **help** command, or with the ``--help`` switch on
any other command::

    $ coverage help
    $ coverage help run
    $ coverage run --help

Version information for coverage.py can be displayed with
``coverage --version``.

Any command can use a configuration file by specifying it with the
``--rcfile=FILE`` command-line switch.  Any option you can set on the command
line can also be set in the configuration file.  This can be a better way to
control coverage.py since the configuration file can be checked into source
control, and can provide options that other invocation techniques (like test
runner plugins) may not offer. See :ref:`config` for more details.


.. _cmd_execution:

Execution
---------

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

If you want :ref:`branch coverage <branch>` measurement, use the ``--branch``
flag.  Otherwise only statement coverage is measured.

You can specify the code to measure with the ``--source``, ``--include``, and
``--omit`` switches.  See :ref:`Specifying source files <source_execution>` for
details of their interpretation.  Remember to put options for run after "run",
but before the program invocation::

    $ coverage run --source=dir1,dir2 my_program.py arg1 arg2
    $ coverage run --source=dir1,dir2 -m packagename.modulename arg1 arg2

Coverage.py can measure multi-threaded programs by default. If you are using
more exotic concurrency, with the `multiprocessing`_, `greenlet`_, `eventlet`_,
or `gevent`_ libraries, then coverage.py will get very confused.  Use the
``--concurrency`` switch to properly measure programs using these libraries.
Give it a value of ``multiprocessing``, ``thread``, ``greenlet``, ``eventlet``,
or ``gevent``.  Values other than ``thread`` require the :ref:`C extension
<install_extension>`.

.. _multiprocessing: https://docs.python.org/2/library/multiprocessing.html
.. _greenlet: http://greenlet.readthedocs.org/en/latest/
.. _gevent: http://www.gevent.org/
.. _eventlet: http://eventlet.net/

By default, coverage.py does not measure code installed with the Python
interpreter, for example, the standard library. If you want to measure that
code as well as your own, add the ``-L`` (or ``--pylib``) flag.

If your coverage results seem to be overlooking code that you know has been
executed, try running coverage.py again with the ``--timid`` flag.  This uses a
simpler but slower trace method.  Projects that use DecoratorTools, including
TurboGears, will need to use ``--timid`` to get correct results.

If you are measuring coverage in a multi-process program, or across a number of
machines, you'll want the ``--parallel-mode`` switch to keep the data separate
during measurement.  See :ref:`cmd_combining` below.

During execution, coverage.py may warn you about conditions it detects that
could affect the measurement process.  The possible warnings include:

* "Trace function changed, measurement is likely wrong: XXX"

  Coverage measurement depends on a Python setting called the trace function.
  Other Python code in your product might change that function, which will
  disrupt coverage.py's measurement.  This warning indicate that has happened.
  The XXX in the message is the new trace function value, which might provide
  a clue to the cause.

* "Module XXX has no Python source"

  You asked coverage.py to measure module XXX, but once it was imported, it
  turned out not to have a corresponding .py file.  Without a .py file,
  coverage.py can't report on missing lines.

* "Module XXX was never imported"

  You asked coverage.py to measure module XXX, but it was never imported by
  your program.

* "No data was collected"

  Coverage.py ran your program, but didn't measure any lines as executed.
  This could be because you asked to measure only modules that never ran,
  or for other reasons.

* "Module XXX was previously imported, but not measured."

  You asked coverage.py to measure module XXX, but it had already been imported
  when coverage started.  This meant coverage.py couldn't monitor its
  execution.


.. _cmd_datafile:

Data file
---------

Coverage.py collects execution data in a file called ".coverage".  If need be,
you can set a new file name with the COVERAGE_FILE environment variable.  This
can include a path to another directory.

By default, each run of your program starts with an empty data set. If you need
to run your program multiple times to get complete data (for example, because
you need to supply disjoint options), you can accumulate data across runs with
the ``-a`` flag on the **run** command.

To erase the collected data, use the **erase** command::

    $ coverage erase


.. _cmd_combining:

Combining data files
--------------------

If you need to collect coverage data from different machines or processes,
coverage.py can combine multiple files into one for reporting.

Once you have created a number of these files, you can copy them all to a
single directory, and use the **combine** command to combine them into one
.coverage data file::

    $ coverage combine

You can also name directories or files on the command line::

    $ coverage combine data1.dat windows_data_files/

Coverage.py will collect the data from those places and combine them.  The
current directory isn't searched if you use command-line arguments.  If you
also want data from the current directory, name it explicitly on the command
line.

When coverage.py looks in directories for data files to combine, even the
current directory, it only reads files with certain names.  It looks for files
named the same as the data file (defaulting to ".coverage"), with a dotted
suffix.  Here are some examples of data files that can be combined::

    .coverage.machine1
    .coverage.20120807T212300
    .coverage.last_good_run.ok

The ``run --parallel-mode`` switch automatically creates separate data files
for each run which can be combined later.  The file names include the machine
name, the process id, and a random number::

    .coverage.Neds-MacBook-Pro.local.88335.316857
    .coverage.Geometer.8044.799674

If the different machines run your code from different places in their file
systems, coverage.py won't know how to combine the data.  You can tell
coverage.py how the different locations correlate with a ``[paths]`` section in
your configuration file.  See :ref:`config_paths` for details.

If any data files can't be read, coverage.py will print a warning indicating
the file and the problem.


.. _cmd_reporting:

Reporting
---------

Coverage.py provides a few styles of reporting, with the **report**, **html**,
**annotate**, and **xml** commands.  They share a number of common options.

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


.. _cmd_summary:

Coverage summary
----------------

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

The ``--skip-covered`` switch will leave out any file with 100% coverage,
letting you focus on the files that still need attention.

Other common reporting options are described above in :ref:`cmd_reporting`.


.. _cmd_html:

HTML annotation
---------------

Coverage.py can annotate your source code for which lines were executed
and which were not.  The **html** command creates an HTML report similar to the
**report** summary, but as an HTML file.  Each module name links to the source
file decorated to show the status of each line.

Here's a `sample report`__.

__ http://nedbatchelder.com/files/sample_coverage_html/index.html

Lines are highlighted green for executed, red for missing, and gray for
excluded.  The counts at the top of the file are buttons to turn on and off
the highlighting.

A number of keyboard shortcuts are available for navigating the report.
Click the keyboard icon in the upper right to see the complete list.

The title of the report can be set with the ``title`` setting in the
``[html]`` section of the configuration file, or the ``--title`` switch on
the command line.

If you prefer a different style for your HTML report, you can provide your
own CSS file to apply, by specifying a CSS file in the ``[html]`` section of
the configuration file.  See :ref:`config_html` for details.

The ``-d`` argument specifies an output directory, defaulting to "htmlcov"::

    $ coverage html -d coverage_html

Other common reporting options are described above in :ref:`cmd_reporting`.

Generating the HTML report can be time-consuming.  Stored with the HTML report
is a data file that is used to speed up reporting the next time.  If you
generate a new report into the same directory, coverage.py will skip
generating unchanged pages, making the process faster.


.. _cmd_annotation:

Text annotation
---------------

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
    -     if 0:   #pragma: no cover
    -         pass
    >     if x == 1:
    !         a = 1
    >     else:
    >         a = 2

Other common reporting options are described above in :ref:`cmd_reporting`.


.. _cmd_xml:

XML reporting
-------------

The **xml** command writes coverage data to a "coverage.xml" file in a format
compatible with `Cobertura`_.

.. _Cobertura: http://cobertura.sourceforge.net

You can specify the name of the output file with the ``-o`` switch.

Other common reporting options are described above in :ref:`cmd_reporting`.


.. _cmd_debug:

Diagnostics
-----------

The **debug** command shows internal information to help diagnose problems.
If you are reporting a bug about coverage.py, including the output of this
command can often help::

    $ coverage debug sys > please_attach_to_bug_report.txt

Two types of information are available: ``sys`` to show system configuration,
and ``data`` to show a summary of the collected coverage data.


.. _cmd_run_debug:

The ``--debug`` option is available on all commands.  It instructs coverage.py
to log internal details of its operation, to help with diagnosing problems.  It
takes a comma-separated list of options, each indicating a facet of operation
to log:

* ``callers``: annotate each debug message with a stack trace of the callers
  to that point.

* ``config``: before starting, dump all the :ref:`configuration <config>`
  values.

* ``dataio``: log when reading or writing any data file.

* ``dataop``: log when data is added to the CoverageData object.

* ``pid``: annotate all debug output with the process id.

* ``plugin``: print information about plugin operations.

* ``sys``: before starting, dump all the system and environment information,
  as with :ref:`coverage debug sys <cmd_debug>`.

* ``trace``: print every decision about whether to trace a file or not. For
  files not being traced, the reason is also given.

Debug options can also be set with the ``COVERAGE_DEBUG`` environment variable,
a comma-separated list of these options.

The debug output goes to stderr, unless the ``COVERAGE_DEBUG_FILE`` environment
variable names a different file, which will be appended to.
