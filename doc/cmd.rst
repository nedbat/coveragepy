.. _cmd:

===========================
Coverage command line usage
===========================

:history: 20090524T134300, brand new docs.
:history: 20090613T164000, final touches for 3.0

.. highlight:: console

When you install coverage, a command-line script called coverage is placed in
the Python scripts directory.  Coverage performs a number of actions, determined
by the flags on the command line:

* -e Erase previously collected coverage data.

* -x Execute a Python program and collect execution data.

* -c Combine together a number of data files.

* -r Report coverage results.

* -a Annotate source files with coverage results.

* -b Produce annotated HTML listings with coverage results.

Some of these can be combined: for example, "-e -x" is the simple way to run a
program without carrying over previous data.


Data file
---------

Coverage collects execution data in a file called ".coverage".  If need be, you can
set a new file name with the COVERAGE_FILE environment variable.  Data accumulates
from run to run, so that you can collect a complete data set of which parts of
your code are executed.

To erase the collected data, use the "-e" command-line switch::

    $ coverage -e



Execution
---------

Coverage collects data by running your Python program with -x::

    $ coverage -x my_program.py arg1 arg2
    blah blah ..your program's output.. blah blah

Your program runs just as if it had been invoked with the Python command line.
Arguments after your file name are passed to your program in sys.argv.

By default, coverage does not measure code installed with the Python interpreter.
If you want to measure that code as well as your own, add the -L flag.

If your coverage results seems to be overlooking code that you know has been
executed, try running coverage again with the --timid flag.  This uses a simpler
but slower trace method.  Projects that use DecoratorTools, including TurboGears,
will need to use --timid to get correct results.  This option can also be set
with the environment variable COVERAGE_OPTIONS set to '--timid'.


Combining data files
--------------------

If you need to collect coverage data from different machines, coverage can
combine multiple files into one for reporting.  Use the -p flag during execution
to append a machine name and process id to the .coverage data file name.

Once you have created a number of these files, you can copy them all to a single
directory, and use the -c flag to combine them into one .coverage data file::

    $ coverage -c


Reporting
---------

Coverage provides a few styles of reporting.  The simplest is a textual summary
produced with -r::

    $ coverage -r
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

The -m flag also shows the line numbers of missing statements::

    $ coverage -r -m 
    Name                      Stmts   Exec  Cover   Missing
    -------------------------------------------------------
    my_program                   20     16    80%   33-35, 39
    my_module                    15     13    86%   8, 12
    my_other_module              56     50    89%   17-23
    -------------------------------------------------------
    TOTAL                        91     79    87%

You can restrict the report to only certain files by naming them on the
command line::

    $ coverage -r -m my_program.py my_other_module.py
    Name                      Stmts   Exec  Cover   Missing
    -------------------------------------------------------
    my_program                   20     16    80%   33-35, 39
    my_other_module              56     50    89%   17-23
    -------------------------------------------------------
    TOTAL                        76     66    87%

The -o flag omits files that begin with specified prefixes. For example, this
will omit any modules in the django directory::

    $ coverage -r -m -o django



HTML annotation
---------------

Coverage can annotate your source code for which lines were executed
and which were not.  The -b flag creates an HTML report similar to the -r
summary, but as an HTML file.  Each module name links to the source file
decorated to show the status of each line.

Here's a `sample report </code/coverage/sample_html/index.html>`_.

Lines are highlighted green for executed, red for missing, and gray for
excluded.  The counts at the top of the file are buttons to turn on and off
the highlighting.

The -d argument to specify an output directory is required::

    $ coverage -b -d covhtml


Text annotation
---------------

The -a flag produces a text annotation of your source code.  With a -d argument
specifying an output directory, each Python file becomes a text file in that
directory.  Without -d, the files are written into the same directories as the
original Python files.

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
  
