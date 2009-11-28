.. _cmd:

===========================
Coverage command line usage
===========================

:history: 20090524T134300, brand new docs.
:history: 20090613T164000, final touches for 3.0
:history: 20090913T084400, new command line syntax
:history: 20091004T170700, changes for 3.1
:history: 20091127T200700, changes for 3.2

.. highlight:: console

When you install coverage.py, a command-line script simply called coverage is
placed in your Python scripts directory.  Coverage has a number of commands
which determine the action performed:

* **run** -- Run a Python program and collect execution data.

* **report** -- Report coverage results.

* **html** -- Produce annotated HTML listings with coverage results.

* **xml** -- Produce an XML report with coverage results.

* **annotate** -- Annotate source files with coverage results.

* **erase** -- Erase previously collected coverage data.

* **combine** -- Combine together a number of data files.

* **debug** -- Get diagnostic information.

Help is available with ``coverage help``, or with the ``--help`` switch on any
other command.


Execution
---------

You collect execution data by running your Python program with the **run**
coverage command::

    $ coverage run my_program.py arg1 arg2
    blah blah ..your program's output.. blah blah

Your program runs just as if it had been invoked with the Python command line.
Arguments after your file name are passed to your program in ``sys.argv``.

If you want :ref:`branch coverage <branch>` measurement, use the ``--branch``
flag.  Otherwise only statement coverage is measured.

By default, coverage does not measure code installed with the Python
interpreter.  If you want to measure that code as well as your own, add the
``-L`` flag.

If your coverage results seems to be overlooking code that you know has been
executed, try running coverage again with the ``--timid`` flag.  This uses a
simpler but slower trace method.  Projects that use DecoratorTools, including
TurboGears, will need to use ``--timid`` to get correct results.  This option
can also be enabled by setting the environment variable COVERAGE_OPTIONS to
``--timid``.


Data file
---------

Coverage collects execution data in a file called ".coverage".  If need be, you
can set a new file name with the COVERAGE_FILE environment variable.  By default,
each run of your program starts with an empty data set. If you need to run your
program multiple times to get complete data (for example, because you need to
supply disjoint options), you can accumulate data across runs with the ``-a``
flag on the **run** command.  

To erase the collected data, use the **erase** command::

    $ coverage erase



Combining data files
--------------------

If you need to collect coverage data from different machines, coverage can
combine multiple files into one for reporting.  Use the ``-p`` flag during
execution to append a machine name and process id to the .coverage data file
name.

Once you have created a number of these files, you can copy them all to a single
directory, and use the **combine** command to combine them into one .coverage
data file.


Reporting
---------

Coverage provides a few styles of reporting.  The simplest is a textual summary
produced with **report**::

    $ coverage report
    Name                      Stmts   Exec  Cover
    ---------------------------------------------
    my_program                   20     16    80%
    my_module                    15     13    86%
    my_other_module              56     50    89%
    ---------------------------------------------
    TOTAL                        91     79    87%

For each module executed, the report shows the count of executable statements,
the number of those statements executed, and the resulting coverage, expressed
as a percentage.

The ``-m`` flag also shows the line numbers of missing statements::

    $ coverage report -m 
    Name                      Stmts   Exec  Cover   Missing
    -------------------------------------------------------
    my_program                   20     16    80%   33-35, 39
    my_module                    15     13    86%   8, 12
    my_other_module              56     50    89%   17-23
    -------------------------------------------------------
    TOTAL                        91     79    87%

You can restrict the report to only certain files by naming them on the
command line::

    $ coverage report -m my_program.py my_other_module.py
    Name                      Stmts   Exec  Cover   Missing
    -------------------------------------------------------
    my_program                   20     16    80%   33-35, 39
    my_other_module              56     50    89%   17-23
    -------------------------------------------------------
    TOTAL                        76     66    87%

The ``--omit`` flag omits files that begin with specified prefixes. For example,
this will omit any modules in the django directory::

    $ coverage report -m --omit django



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

The ``-d`` argument specifies an output directory, and is required::

    $ coverage html -d covhtml


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
  

XML reporting
-------------

The **xml** command writes coverage data to a "coverage.xml" file in a format
compatible with `Cobertura`_.

.. _Cobertura: http://cobertura.sourceforge.net


Diagnostics
-----------

The **debug** command shows internal information to help diagnose problems.

