.. _faq:

==================
FAQ and other help
==================

.. :history: 20090613T141800, brand new docs.
.. :history: 20091005T073900, updated for 3.1.
.. :history: 20091127T201500, updated for 3.2.
.. :history: 20110605T175500, add the announcement mailing list.
.. :history: 20121231T104700, Tweak the py3 text.


Frequently asked questions
--------------------------

**Q: I use nose to run my tests, and its cover plugin doesn't let me create
HTML or XML reports.  What should I do?**

First run your tests and collect coverage data with `nose`_ and its plugin.
This will write coverage data into a .coverage file.  Then run coverage.py from
the :ref:`command line <cmd>` to create the reports you need from that data.

.. _nose: http://somethingaboutorange.com/mrl/projects/nose


**Q: Why do unexecutable lines show up as executed?**

Usually this is because you've updated your code and run coverage on it again
without erasing the old data.  Coverage records line numbers executed, so the
old data may have recorded a line number which has since moved, causing
coverage to claim a line has been executed which cannot be.

If you are using the ``-x`` command line action, it doesn't erase first by
default.  Switch to the ``coverage run`` command, or use the ``-e`` switch to
erase all data before starting the next run.


**Q: Why do the bodies of functions (or classes) show as executed, but the def
lines do not?**

This happens because coverage is started after the functions are defined.  The
definition lines are executed without coverage measurement, then coverage is
started, then the function is called.  This means the body is measured, but
the definition of the function itself is not.

To fix this, start coverage earlier.  If you use the :ref:`command line <cmd>`
to run your program with coverage, then your entire program will be monitored.
If you are using the :ref:`API <api>`, you need to call coverage.start() before
importing the modules that define your functions.


**Q: Coverage is much slower than I remember, what's going on?**

Make sure you are using the C trace function.  Coverage.py provides two
implementations of the trace function.  The C implementation runs much faster.
To see what you are running, use ``coverage debug sys``.  The output contains
details of the environment, including a line that says either ``tracer: CTracer``
or ``tracer: PyTracer``.  If it says ``PyTracer`` then you are using the
slow Python implementation.

Try re-installing coverage.py to see what happened and if you get the CTracer
as you should.


**Q: Does coverage.py work on Python 3.x?**

Yes, Python 3 is fully supported.


**Q: Isn't coverage testing the best thing ever?**

It's good, but `it isn't perfect`__.

__ http://nedbatchelder.com/blog/200710/flaws_in_coverage_measurement.html


..  Other resources
    ---------------

    There are a number of projects that help integrate coverage.py into other
    systems:

    - `trialcoverage`_ is a plug-in for Twisted trial.

    .. _trialcoverage: http://pypi.python.org/pypi/trialcoverage

    - `pytest-coverage`_

    .. _pytest-coverage: http://pypi.python.org/pypi/pytest-coverage

    - `django-coverage`_ for use with Django.

    .. _django-coverage: http://pypi.python.org/pypi/django-coverage


**Q: Where can I get more help with coverage.py?**

You can discuss coverage.py or get help using it on the `Testing In Python`_
mailing list.

.. _Testing In Python: http://lists.idyll.org/listinfo/testing-in-python

Bug reports are gladly accepted at the `Bitbucket issue tracker`_.

.. _Bitbucket issue tracker: http://bitbucket.org/ned/coveragepy/issues

Announcements of new coverage.py releases are sent to the
`coveragepy-announce`_ mailing list.

.. _coveragepy-announce: http://groups.google.com/group/coveragepy-announce

`I can be reached`__ in a number of ways, I'm happy to answer questions about
using coverage.py.

__  http://nedbatchelder.com/site/aboutned.html


History
-------

Coverage.py was originally written by `Gareth Rees`_.
Since 2004, `Ned Batchelder`_ has extended and maintained it with the help of
`many others`_.  The :ref:`change history <changes>` has all the details.

.. _Gareth Rees:    http://garethrees.org/
.. _Ned Batchelder: http://nedbatchelder.com
.. _many others:    http://bitbucket.org/ned/coveragepy/src/tip/AUTHORS.txt
