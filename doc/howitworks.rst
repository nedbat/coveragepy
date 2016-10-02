.. Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
.. For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

.. _howitworks:

=====================
How Coverage.py works
=====================

.. :history: 20150812T071000, new page.

For advanced use of coverage.py, or just because you are curious, it helps to
understand what's happening behind the scenes.  Coverage.py works in three
phases:

* **Execution**: Coverage.py runs your code, and monitors it to see what lines
  were executed.

* **Analysis**: Coverage.py examines your code to determine what lines could
  have run.

* **Reporting**: Coverage.py combines the results of execution and analysis to
  produce a coverage number and an indication of missing execution.

The execution phase is handled by the ``coverage run`` command.  The analysis
and reporting phases are handled by the reporting commands like ``coverage
report`` or ``coverage html``.

Let's look at each phase in more detail.


Execution
---------

At the heart of the execution phase is a Python trace function.  This is a
function that the Python interpreter invokes for each line executed in a
program.  Coverage.py implements a trace function that records each file and
line number as it is executed.

Executing a function for every line in your program can make execution very
slow.  Coverage.py's trace function is implemented in C to reduce that
slowdown. It also takes care to not trace code that you aren't interested in.

When measuring branch coverage, the same trace function is used, but instead of
recording line numbers, coverage.py records pairs of line numbers.  Each
invocation of the trace function remembers the line number, then the next
invocation records the pair `(prev, this)` to indicate that execution
transitioned from the previous line to this line.  Internally, these are called
arcs.

For more details of trace functions, see the Python docs for `sys.settrace`_,
or if you are really brave, `How C trace functions really work`_.

At the end of execution, coverage.py writes the data it collected to a data
file, usually named ``.coverage``.  This is a JSON-based file containing all of
the recorded file names and line numbers executed.

.. _sys.settrace: https://docs.python.org/3/library/sys.html#sys.settrace
.. _How C trace functions really work: http://nedbatchelder.com/text/trace-function.html


Analysis
--------

After your program has been executed and the line numbers recorded, coverage.py
needs to determine what lines could have been executed.  Luckily, compiled
Python files (.pyc files) have a table of line numbers in them.  Coverage.py
reads this table to get the set of executable lines, with a little more source
analysis to leave out things like docstrings.

The data file is read to get the set of lines that were executed.  The
difference between the executable lines, and the executed lines, are the lines
that were not executed.

The same principle applies for branch measurement, though the process for
determining possible branches is more involved.  Coverage.py uses the abstract
syntax tree of the Python source file to determine the set of possible
branches.


Reporting
---------

Once we have the set of executed lines and missing lines, reporting is just a
matter of formatting that information in a useful way.  Each reporting method
(text, html, annotated source, xml) has a different output format, but the
process is the same: write out the information in the particular format,
possibly including the source code itself.


Plugins
-------

Plugins interact with these phases.
