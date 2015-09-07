.. Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
.. For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

.. _contributing:

===========================
Contributing to coverage.py
===========================

.. :history: 20121112T154100, brand new docs.

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
        $ cd coveragepy

#.  Install the requirements::

        $ pip install -r requirements/dev.pip

#.  Install a number of versions of Python.  Coverage.py supports a wide range
    of Python versions.  The more you can test with, the more easily your code
    can be used as-is.  If you only have one version, that's OK too, but may
    mean more work integrating your contribution.


Running the tests
-----------------

The tests are written as standard unittest-style tests, and are run with
`tox`_::

    $ tox
    py27 create: /Users/ned/coverage/trunk/.tox/py27
    py27 installdeps: nose==1.3.7, mock==1.3.0, PyContracts==1.7.6, gevent==1.0.2, eventlet==0.17.4, greenlet==0.4.7
    py27 develop-inst: /Users/ned/coverage/trunk
    py27 installed: -f /Users/ned/Downloads/local_pypi,-e hg+ssh://hg@bitbucket.org/ned/coveragepy@22fe9a2b7796f6498aa013c860c268ac21651226#egg=coverage-dev,decorator==4.0.2,eventlet==0.17.4,funcsigs==0.4,gevent==1.0.2,greenlet==0.4.7,mock==1.3.0,nose==1.3.7,pbr==1.6.0,PyContracts==1.7.6,pyparsing==2.0.3,six==1.9.0,wheel==0.24.0
    py27 runtests: PYTHONHASHSEED='1294330776'
    py27 runtests: commands[0] | python setup.py --quiet clean develop
    py27 runtests: commands[1] | python igor.py zip_mods install_egg remove_extension
    py27 runtests: commands[2] | python igor.py test_with_tracer py
    === CPython 2.7.10 with Python tracer (.tox/py27/bin/python) ===
    ............................................................................(etc)
    ----------------------------------------------------------------------
    Ran 592 tests in 65.524s

    OK (SKIP=20)
    py27 runtests: commands[3] | python setup.py --quiet build_ext --inplace
    py27 runtests: commands[4] | python igor.py test_with_tracer c
    === CPython 2.7.10 with C tracer (.tox/py27/bin/python) ===
    ............................................................................(etc)
    ----------------------------------------------------------------------
    Ran 592 tests in 69.635s

    OK (SKIP=4)
    py33 create: /Users/ned/coverage/trunk/.tox/py33
    py33 installdeps: nose==1.3.7, mock==1.3.0, PyContracts==1.7.6, greenlet==0.4.7
    py33 develop-inst: /Users/ned/coverage/trunk
    py33 installed: -f /Users/ned/Downloads/local_pypi,-e hg+ssh://hg@bitbucket.org/ned/coveragepy@22fe9a2b7796f6498aa013c860c268ac21651226#egg=coverage-dev,decorator==4.0.2,greenlet==0.4.7,mock==1.3.0,nose==1.3.7,pbr==1.6.0,PyContracts==1.7.6,pyparsing==2.0.3,six==1.9.0,wheel==0.24.0
    py33 runtests: PYTHONHASHSEED='1294330776'
    py33 runtests: commands[0] | python setup.py --quiet clean develop
    py33 runtests: commands[1] | python igor.py zip_mods install_egg remove_extension
    py33 runtests: commands[2] | python igor.py test_with_tracer py
    === CPython 3.3.6 with Python tracer (.tox/py33/bin/python) ===
    ............................................S...............................(etc)
    ----------------------------------------------------------------------
    Ran 592 tests in 73.007s

    OK (SKIP=22)
    py33 runtests: commands[3] | python setup.py --quiet build_ext --inplace
    py33 runtests: commands[4] | python igor.py test_with_tracer c
    === CPython 3.3.6 with C tracer (.tox/py33/bin/python) ===
    ............................................S...............................(etc)
    ----------------------------------------------------------------------
    Ran 592 tests in 72.071s

    OK (SKIP=5)
    (and so on...)

Tox runs the complete test suite twice for each version of Python you have
installed.  The first run uses the Python implementation of the trace function,
the second uses the C implementation.

To limit tox to just a few versions of Python, use the ``-e`` switch::

    $ tox -e py27,py33

To run just a few tests, you can use nose test selector syntax::

    $ tox tests.test_misc:SetupPyTest.test_metadata

This looks in `tests/test_misc.py` to find the `SetupPyTest` class, and runs
the `test_metadata` test method.

Of course, run all the tests on every version of Python you have, before
submitting a change.


Lint, etc
---------

I try to keep the coverage.py as clean as possible.  I use pylint to alert me
to possible problems::

    $ make lint
    pylint coverage setup.py tests
    python -m tabnanny coverage setup.py tests
    python igor.py check_eol

The source is pylint-clean, even if it's because there are pragmas quieting
some warnings.  Please try to keep it that way, but don't let pylint warnings
keep you from sending patches.  I can clean them up.

Lines should be kept to a 100-character maximum length.


Coverage testing coverage.py
----------------------------

Coverage.py can measure itself, but it's complicated.  The process has been
packaged up to make it easier::

    $ make metacov metahtml

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
