.. _trouble:

====================
When things go wrong
====================

Coverage works pretty well, but occasionally things don't go as you would like.
This page details problems, with links to coverage.py bug reports if
appropriate.

You can of course search the `coverage.py bug tracker`_ directly to see if 
there is some mention of your problem.

.. _coverage.py bug tracker: https://bitbucket.org/ned/coveragepy/issues?status=new&status=open


Kryptonite
----------

There are a number of popular packages that prevent coverage.py from working 
properly.  

* gevent, `issue 149`_.

* execv, or one of its variants, `issue 43`_.

* multiprocessing, `issue 117`_.

Code is marked as not executed when I know it is.

link to DecoratorTools, TurboGears

Try --timid

psyco is an issue?

.. _issue 43: https://bitbucket.org/ned/coveragepy/issue/43/coverage-measurement-fails-on-code
.. _issue 117: https://bitbucket.org/ned/coveragepy/issue/117/enable-coverage-measurement-of-code-run-by
.. _issue 149: https://bitbucket.org/ned/coveragepy/issue/149/coverage-gevent-looks-broken


Really obscure stuff
--------------------

* Python 2.5 had a bug (`1569356`_) that could make your program behave
  differently when being measured with coverage.  This is diagnosed in `issue 51`_.

.. _issue 51: http://bitbucket.org/ned/coveragepy/issue/51/turbogears-15-test-failing-with-coverage
.. _1569356: http://bugs.python.org/issue1569356
