.. _cmd:

===========================
Coverage command line usage
===========================

:history: 20090524T134300, brand new docs.
:history: 20090613T164000, final touches for 3.0
:history: 20090913T084400, new command line syntax
:history: 20091004T170700, changes for 3.1
:history: 20091127T200700, changes for 3.2
:history: 20100223T200600, changes for 3.3
:history: 20100725T211700, updated for 3.4

.. highlight:: console


When you install coverage.py, a command-line script simply called ``coverage``
is placed in your Python scripts directory.  Coverage has a number of commands
which determine the action performed:

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
``sys.argv``.  Rather than providing a filename, you can use the ``-m`` switch
and specify an importable module name instead, just as you can with the
Python ``-m`` switch.

If you want :ref:`branch coverage <branch>` measurement, use the ``--branch``
flag.  Otherwise only statement coverage is measured.

You can specify the code to measure with the ``--source``, ``--include``, and
``--omit`` switches.  See :ref:`Specifying source files <source_execution>` for
more details.

By default, coverage does not measure code installed with the Python
interpreter, for example, the standard library. If you want to measure that
code as well as your own, add the ``-L`` flag.

If your coverage results seem to be overlooking code that you know has been
executed, try running coverage again with the ``--timid`` flag.  This uses a
simpler but slower trace method.  Projects that use DecoratorTools, including
TurboGears, will need to use ``--timid`` to get correct results.  This option
can also be enabled by setting the environment variable COVERAGE_OPTIONS to
``--timid``.

If you are measuring coverage in a multi-process program, or across a number of
machines, you'll want the ``--parallel-mode`` switch to keep the data separate
during measurement.  See :ref:`cmd_combining` below.

During execution, coverage.py may warn you about conditions it detects that
could affect the measurement process.  The possible warnings include:

* "Trace function changed, measurement is likely wrong"

* "Module has no Python source"

* "Module was never imported"

* "No data was collected"



.. _cmd_datafile:

Data file
---------

Coverage collects execution data in a file called ".coverage".  If need be, you
can set a new file name with the COVERAGE_FILE environment variable.

By default,each run of your program starts with an empty data set. If you need
to run your program multiple times to get complete data (for example, because
you need to supply disjoint options), you can accumulate data across runs with
the ``-a`` flag on the **run** command.

To erase the collected data, use the **erase** command::

    $ coverage erase


.. _cmd_combining:

Combining data files
--------------------

If you need to collect coverage data from different machines or processes,
coverage can combine multiple files into one for reporting. Use the ``-p`` flag
during execution to append distinguishing information to the .coverage data
file name.

Once you have created a number of these files, you can copy them all to a single
directory, and use the **combine** command to combine them into one .coverage
data file::

    $ coverage combine


.. _cmd_reporting:

Reporting
---------

Coverage provides a few styles of reporting, with the **report**, **html**,
**annotate**, and **xml** commands.  They share a number of common options.

The command-line arguments are module or file names to report on, if you'd like
to report on a subset of the data collected.

The ``--include`` and ``--omit`` flags specify lists of filename patterns. They
control which files to report on, and are described in more detail
in :ref:`source`.

The ``-i`` or ``--ignore-errors`` switch tells coverage.py to ignore problems
encountered trying to find source files to report on.  This can be useful if
some files are missing, or if your Python execution is tricky enough that file
names are synthesized without real source files.



.. _cmd_summary:

Coverage summary
----------------

The simplest reporting is a textual summary produced with **report**::

    $ coverage report
    Name                      Stmts   Miss  Cover
    ---------------------------------------------
    my_program                   20      4    80%
    my_module                    15      2    86%
    my_other_module              56      6    89%
    ---------------------------------------------
    TOTAL                        91     12    87%

For each module executed, the report shows the count of executable statements,
the number of those statements missed, and the resulting coverage, expressed
as a percentage.

The ``-m`` flag also shows the line numbers of missing statements::

    $ coverage report -m
    Name                      Stmts   Miss  Cover   Missing
    -------------------------------------------------------
    my_program                   20      4    80%   33-35, 39
    my_module                    15      2    86%   8, 12
    my_other_module              56      6    89%   17-23
    -------------------------------------------------------
    TOTAL                        91     12    87%

You can restrict the report to only certain files by naming them on the
command line::

    $ coverage report -m my_program.py my_other_module.py
    Name                      Stmts   Miss  Cover   Missing
    -------------------------------------------------------
    my_program                   20      4    80%   33-35, 39
    my_other_module              56      6    89%   17-23
    -------------------------------------------------------
    TOTAL                        76     10    87%

Other common reporting options are described above in :ref:`cmd_reporting`.


.. _cmd_html:

HTML annotation
---------------

Coverage can annotate your source code for which lines were executed
and which were not.  The **html** command creates an HTML report similar to the
**report** summary, but as an HTML file.  Each module name links to the source
file decorated to show the status of each line.

Here's a `sample report`__.

__ /code/coverage/sample_html/index.html

Lines are highlighted green for executed, red for missing, and gray for
excluded.  The counts at the top of the file are buttons to turn on and off
the highlighting.

A number of keyboard shortcuts are available for navigating the report.
Click the keyboard icon in the upper right to see the complete list.

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

The **annotate** command produces a text annotation of your source code.  With a
``-d`` argument specifying an output directory, each Python file becomes a text
file in that directory.  Without ``-d``, the files are written into the same
directories as the original Python files.

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

You can specify the name of the output file with the ``--output-xml`` switch.

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
