.. _branch:

===========================
Branch coverage measurement
===========================

:history: 20091127T201300, new for version 3.2


Coverage.py now supports branch coverage measurement.  Where a line in your
program could jump to more than one next line, coverage.py tracks which of
those destinations are actually visited, and flags lines that haven't visited
all of their possible destinations.

For example::

    def my_partial_fn(x):       # line 1
        if x:                   #      2
            y = 10              #      3
        return y                #      4
        
    my_partial_fn(1)
    
In this code, line 2 is an ``if`` statement which can go next to either line 3
or line 4. Statement coverage would show all lines of the function as executed.
But the if was never evaluated as false, so line 2 never jumps to line 4.

Branch coverage will flag this code as not fully covered because of the missing
jump from line 2 to line 4.


How to measure branch coverage
------------------------------

To measure branch coverage, run coverage.py with the ``--branch`` flag::

    coverage run --branch myprog.py
    
When you report on the results with "coverage report" or "coverage html", the
percentage of branch possibilities taken will be included in the percentage
covered total for each file.  The coverage percentage for a file is the
actual executions divided by the execution opportunities.  Each line in the
file is an execution opportunity, as is each branch destination.

The HTML report gives information about which lines had missing branches. Lines
that were missing some branches are shown in yellow, with an annotation at the
far right showing branch destination line numbers that were not exercised.

The XML report produced by "coverage xml" also includes branch information,
including separate statement and branch coverage percentages.  Each line is
annotated with 


How it works
------------

When measuring branches, coverage.py collects pairs of line numbers, a source
and destination for each transition from one line to another.  Static analysis
of the compiled bytecode provides a list of possible transitions.  Comparing
the measured to the possible indicates missing branches.

The idea of tracking how lines follow each other was from C. Titus Brown.
Thanks, Titus!


Excluding code
--------------

If you have excluded 
Problems
--------

Some Python constructs are difficult to measure properly.  For example, an
unconditional loop will be marked as partially executed::

    while True:                         # line 1
        if some_condition():            #      2
            break                       
        body_of_loop()                  #      4
    
    keep_working()                      #      6

Because the loop never terminates naturally (jumping from line 1 to 6),
coverage.py considers the branch partially executed. 
