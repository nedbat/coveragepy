.. _trouble:

=========================
Things that cause trouble
=========================

.. :history: 20121231T085200, brand new docs.
.. :history: 20150124T160800, remove obsolete stuff.


Coverage works well, and I want it to properly measure any Python program, but
there are some situations it can't cope with.  This page details some known
problems, with possible courses of action, and links to coverage.py bug reports
with more information.

I would love to :ref:`hear from you <contact>` if you have information about
any of these problems, even just to explain to me why you want them to start
working properly.

If your problem isn't discussed here, you can of course search the `coverage.py
bug tracker`_ directly to see if there is some mention of it.

.. _coverage.py bug tracker: https://bitbucket.org/ned/coveragepy/issues?status=new&status=open


Things that don't work
----------------------

There are a number of popular modules, packages, and libraries that prevent
coverage.py from working properly:

* `execv`_, or one of its variants.  These end the current program and replace
  it with a new one.  This doesn't save the collected coverage data, so your
  program that calls execv will not be fully measured.  A patch for coverage.py
  is in `issue 43`_.

* `thread`_, in the Python standard library, is the low-level threading
  interface.  Threads created with this module will not be traced.  Use the
  higher-level `threading`_ module instead.

* `sys.settrace`_ is the Python feature that coverage.py uses to see what's
  happening in your program.  If another part of your program is using
  sys.settrace, then it will conflict with coverage.py, and it won't be
  measured properly.

.. _execv: http://docs.python.org/library/os#os.execl
.. _sys.settrace: http://docs.python.org/library/sys.html#sys.settrace
.. _thread: http://docs.python.org/library/thread.html
.. _threading: http://docs.python.org/library/threading.html
.. _issue 43: https://bitbucket.org/ned/coveragepy/issue/43/coverage-measurement-fails-on-code


Things that require --timid
---------------------------

Some packages interfere with coverage measurement, but you might be able to
make it work by using the ``--timid`` command-line switch, or the ``[run]
timid=True`` configuration option.

* `DecoratorTools`_, or any package which uses it, notably `TurboGears`_.
  DecoratorTools fiddles with the trace function.  You  will need to use
  ``--timid``.

.. _DecoratorTools: http://pypi.python.org/pypi/DecoratorTools
.. _TurboGears: http://turbogears.org/


Still having trouble?
---------------------

If your problem isn't mentioned here, and isn't already reported in the
`coverage.py bug tracker`_, please :ref:`get in touch with me <contact>`,
we'll figure out a solution.
