.. _contributing:

===========================
Contributing to coverage.py
===========================

:history: 20121112T154100, brand new docs.

.. highlight:: console

I welcome contributions to coverage.py.  Over the years, dozens of people have
provided patches of various sizes to add features or fix bugs.  This page
should have all the information you need to make a contribution.

One source of history or ideas are the `bug reports`_ against coverage.py.
There you can find ideas for requested features, or the remains of rejected
ideas.

.. _bug reports: https://bitbucket.org/ned/coveragepy/issues?status=new&status=open


Before you begin
----------------

If you have an idea for coverage.py, run it by me before you begin writing
code.  This way, I can get you going in the right direction, or point you to
previous work in the area.  Things are not always as straightforward as they
seem, and having the benefit of lessons learned by those before you can save
you frustration.


Getting the code
----------------

The coverage.py code is hosted on a `Mercurial`_ repository at
https://bitbucket.org/ned/coveragepy.  To get a working environment, follow
these steps:

#.  (Optional, but recommended) Create a virtualenv to work in, and activate
    it.

#.  Clone the repo::

        $ hg clone https://bitbucket.org/ned/coveragepy

#.  Install the requirements::

        $ pip install -r requirements.txt

#.  Install a number of versions of Python.  Coverage.py supports a wide range
    of Python versions.  The more you can test with, the more easily your code
    can be used as-is.  If you only have one version, that's OK too, but may
    mean more work integrating your contribution.


Running the tests
-----------------

The tests are written as standard unittest-style tests, and are run with
`tox`_::

    $ tox
    GLOB sdist-make: /home/ned/coverage/setup.py
    py25 sdist-reinst: /home/ned/coverage/tox/dist/coverage-3.6b1.zip
    py25 runtests: commands[0]
    py25 runtests: commands[1]
    py25 runtests: commands[2]
    py25 runtests: commands[3]
    py25 runtests: commands[4]
    === Python 2.5.5 with Python tracer (/home/ned/coverage/tox/py25/bin/python) ===
    ...........................................................................................(etc)
    ----------------------------------------------------------------------
    Ran 360 tests in 10.836s

    OK
    py25 runtests: commands[5]
    py25 runtests: commands[6]
    === Python 2.5.5 with C tracer (/home/ned/coverage/tox/py25/bin/python) ===
    ...........................................................................................(etc)
    ----------------------------------------------------------------------
    Ran 360 tests in 10.044s

    OK
    py26 sdist-reinst: /home/ned/coverage/trunk/.tox/dist/coverage-3.6b1.zip
    py26 runtests: commands[0]
    py26 runtests: commands[1]
    py26 runtests: commands[2]
    py26 runtests: commands[3]
    py26 runtests: commands[4]
    === CPython 2.6.6 with Python tracer (/home/ned/coverage/tox/py26/bin/python) ===
    ...........................................................................................(etc)
    ----------------------------------------------------------------------
    Ran 364 tests in 12.572s

    OK
    py26 runtests: commands[5]
    py26 runtests: commands[6]
    === CPython 2.6.6 with C tracer (/home/ned/coverage/tox/py26/bin/python) ===
    ...........................................................................................(etc)
    ----------------------------------------------------------------------
    Ran 364 tests in 11.458s

    OK
    (and so on...)

Tox runs the complete test suite twice for each version of Python you have
installed.  The first run uses the Python implementation of the trace
function, the second uses the C implementation.

To limit tox to just a few versions of Python, use the ``-e`` switch::

    $ tox -e py27,py33

To run just a few tests, you can use nose test selector syntax::

    $ tox test.test_misc:SetupPyTest.test_metadata

This looks in `test/test_misc.py` to find the `SetupPyTest` class, and runs the
`test_metadata` test method.

Of course, run all the tests on every version of Python you have, before
submitting a change.


Lint, etc
---------

I try to keep the coverage.py as clean as possible.  I use pylint to alert me
to possible problems::

    $ make lint
    pylint --rcfile=.pylintrc coverage setup.py test
    python -m tabnanny coverage setup.py test
    python igor.py check_eol

The source is pylint-clean, even if it's because there are pragmas quieting
some warnings.  Please try to keep it that way, but don't let pylint warnings
keep you from sending patches.  I can clean them up.


Coverage testing coverage.py
----------------------------

Coverage.py can measure itself, but it's complicated.  The process has been
packaged up to make it easier::

    $ COVERAGE_COVERAGE=yes tox
    $ python igor.py combine_html

Then look at htmlcov/index.html.  Note that due to the recursive nature of
coverage.py measuring itself, there are some parts of the code that will never
appear as covered, even though they are executed.


Contributing
------------

When you are ready to contribute a change, any way you can get it to me is
probably fine.  A pull request on Bitbucket is great, but a simple diff or
patch is great too.


.. _Mercurial: http://mercurial.selenic.com/
.. _tox: http://tox.testrun.org/
