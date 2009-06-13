.. _excluding:

============================
Excluding code from coverage
============================

:history: 20090613T090500, brand new docs.

You may have code in your project that you know won't be executed, and you want
to tell coverage to ignore it.  For example, you may have debugging-only code
that won't be executed during your unit tests. You can tell coverage to exclude
this code during reporting so that it doesn't clutter your reports with noise
about code that you don't need to hear about.

Coverage will look for comments marking clauses for exclusion.  In this code,
the "if debug" clause is excluded from reporting::

    a = my_function1()
    if debug:   # pragma: no cover
        msg = "blah blah"
        log_message(msg, a)
    b = my_function2()
        
Any line with a comment of "pragma: no cover" is excluded.  If that line
introduces a clause, for example, an if clause, or a function or class
definition, then the entire clause is also excluded.  Here the __repr__
function is not reported as missing::

    class MyObject(object):
        def __init__(self):
            blah1()
            blah2()
            
        def __repr__(self): # pragma: no cover
            return "<MyObject>"

Excluded code is executed as usual, and its execution is recorded in the
coverage data as usual. When producing reports though, coverage excludes it from
the list of missing code.


Advanced exclusion
------------------

Coverage identifies exclusions by matching lines against a list of regular
expressions.  Using the coverage :ref:`API <api>`, you can add to that list.
This is useful if you have often-used constructs to exclude that can be matched
with a regex. You can exclude them all at once without littering your code with
exclusion pragmas.

For example, you might decide that __repr__ functions are usually only used
in debugging code, and are uninteresting to test themselves.  You could exclude
all of them by adding a regex to the exclusion list::

    coverage.exclude("def __repr__")
    
Here's a list of exclusions I've used::

    coverage.exclude('def __repr__')
    coverage.exclude('if self.debug:')
    coverage.exclude('if settings.DEBUG')
    coverage.exclude('raise AssertionError')
    coverage.exclude('raise NotImplementedError')
    coverage.exclude('if 0:')
    coverage.exclude('if __name__ == .__main__.:')

