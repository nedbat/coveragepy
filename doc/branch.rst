.. _branch:

===========================
Branch coverage measurement
===========================

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
    
In this code, the if on line 2 could branch to either line 3 or line 4.
Statement coverage would show all lines of the function as executed.  But the
if is always true, so line 2 never jumps to line 4.  Even though line 4 is
executed, coverage.py knows that it was never because of a branch from line
2.

Branch coverage would flag this code as not fully covered because of the
missing jump from line 2 to line 4.


How to measure branch coverage
------------------------------

To measure branch coverage, run coverage.py with the --branch flag::

    coverage run --branch myprog.py
    
When you report on the results with "coverage report" or "coverage html", the
percentage of branch possibilities taken will be included in the percentage
covered total for each file.  The coverage percentage for a file is the
actual executions divided by the execution opportunities.  Each line in the
file is an execution opportunity, as is each branch destination.

Currently, only HTML reports give information about which lines had missing
branches.  Lines that were missing some branches are shown in yellow, with an
annotation at the far right showing branch destination line numbers that were
not exercised.


How it works
------------

When measuring branches, coverage.py collects pairs of line numbers, a source
and destination for each transition from one line to another.  Static analysis
of the compiled bytecode provides a list of possible transitions.  Comparing
the measured to the possible indicates missing branches.

The idea of tracking how lines follow each other was from C. Titus Brown.
Thanks, Titus!


Problems
--------

Some Python constructs are difficult to measure properly.  For example, an
infinite loop will be marked as partially executed::

    while True:                         # line 1
        if some_condition():            #      2
            break                       
        body_of_loop()                  #      4
    
    keep_working()                      #      6

Because the loop never terminates naturally (jumping from line 1 to 6),
coverage.py thinks the branch is partially executed. 

Currently, if you exclude code from coverage testing, a branch into that code
will still be considered executable, and may result in the branch being
flagged.


Other work
----------

One interesting side effect of tracking line transitions: we know where some
exceptions happened because a transition happens that wasn't predicted by the
static analysis.  Currently, I'm not doing anything with this information.
Any ideas?
