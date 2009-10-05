.. _faq:

==================
FAQ and other help
==================

:history: 20090613T141800, brand new docs.

Frequently asked questions
--------------------------


**Q: I use `nose`_ to run my tests, and the ``--with-cover`` plugin doesn't let
me create HTML or XML reports.  What should I do?**

.. _nose: http://somethingaboutorange.com/mrl/projects/nose

First run your tests and collect coverage data with nose and its plugin.  This
will write coverage data into a .coverage file.  Then run coverage.py from the
command line to create the reports you need from that data.


**Q: Why do unexecutable lines show up as executed?**

Usually this is because you've updated your code and run coverage on it
again without erasing the old data.  Coverage records line numbers executed, so
the old data may have recorded a line number which has since moved, causing
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


**Q: Does coverage.py work on Python 3.x?**

Yes, as of coverage.py 3.1, Python 3.1 is supported.


**Q: Isn't coverage testing the best thing ever?**

It's good, but `it isn't perfect
<http://nedbatchelder.com/blog/200710/flaws_in_coverage_measurement.html>`_.


Getting more help
-----------------

You can discuss coverage or get help using it on the `Testing In Python
<http://lists.idyll.org/listinfo/testing-in-python>`_ mailing list.

Bug reports are gladly accepted at the `bitbucket issue tracker
<http://bitbucket.org/ned/coveragepy/issues/>`_.  Bitbucket also hosts the
`code repository <http://bitbucket.org/ned/coveragepy>`_.

Lastly, `I can be reached <http://nedbatchelder.com/site/aboutned.html>`_ in a
number of ways.
