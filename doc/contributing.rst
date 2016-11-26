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

.. like this:
 mkvirtualenv -p /usr/local/pythonz/pythons/CPython-2.7.11/bin/python coverage

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
    py27 develop-inst-noop: /Users/ned/coverage/trunk
    py27 installed: apipkg==1.4,-e hg+ssh://hg@bitbucket.org/ned/coveragepy@6664140e34beddd6fee99b729bb9f4545a429c12#egg=coverage,covtestegg1==0.0.0,decorator==4.0.10,eventlet==0.19.0,execnet==1.4.1,funcsigs==1.0.2,gevent==1.1.2,greenlet==0.4.10,mock==2.0.0,pbr==1.10.0,py==1.4.31,PyContracts==1.7.12,pyparsing==2.1.10,pytest==3.0.5.dev0,pytest-warnings==0.2.0,pytest-xdist==1.15.0,six==1.10.0,unittest-mixins==1.1.1
    py27 runtests: PYTHONHASHSEED='4113423111'
    py27 runtests: commands[0] | python setup.py --quiet clean develop
    no previously-included directories found matching 'tests/eggsrc/dist'
    no previously-included directories found matching 'tests/eggsrc/*.egg-info'
    py27 runtests: commands[1] | python igor.py zip_mods install_egg remove_extension
    py27 runtests: commands[2] | python igor.py test_with_tracer py
    === CPython 2.7.12 with Python tracer (.tox/py27/bin/python) ===
    gw0 [679] / gw1 [679] / gw2 [679]
    scheduling tests via LoadScheduling
    ...........ss...................................................................................ss...s.......s...........................s...............................................................................s.....................................................................................................................................................s.........................................................................................s.s.s.s.s.ssssssssssss.ss..................................................s...................................................................s..............................................................................
    649 passed, 30 skipped in 42.89 seconds
    py27 runtests: commands[3] | python setup.py --quiet build_ext --inplace
    py27 runtests: commands[4] | python igor.py test_with_tracer c
    === CPython 2.7.12 with C tracer (.tox/py27/bin/python) ===
    gw0 [679] / gw1 [679] / gw2 [679]
    scheduling tests via LoadScheduling
    ............ss................................................................................s..s.....s......s.........................s..........................................................................................s............................................................................................................s............................................................................................................................s...................................................................s........................................................................s............................................................................
    667 passed, 12 skipped in 41.87 seconds
    py35 develop-inst-noop: /Users/ned/coverage/trunk
    py35 installed: apipkg==1.4,-e hg+ssh://hg@bitbucket.org/ned/coveragepy@6664140e34beddd6fee99b729bb9f4545a429c12#egg=coverage,covtestegg1==0.0.0,decorator==4.0.10,eventlet==0.19.0,execnet==1.4.1,gevent==1.1.2,greenlet==0.4.10,mock==2.0.0,pbr==1.10.0,py==1.4.31,PyContracts==1.7.12,pyparsing==2.1.10,pytest==3.0.5.dev0,pytest-warnings==0.2.0,pytest-xdist==1.15.0,six==1.10.0,unittest-mixins==1.1.1
    py35 runtests: PYTHONHASHSEED='4113423111'
    py35 runtests: commands[0] | python setup.py --quiet clean develop
    no previously-included directories found matching 'tests/eggsrc/dist'
    no previously-included directories found matching 'tests/eggsrc/*.egg-info'
    py35 runtests: commands[1] | python igor.py zip_mods install_egg remove_extension
    py35 runtests: commands[2] | python igor.py test_with_tracer py
    === CPython 3.5.2 with Python tracer (.tox/py35/bin/python) ===
    gw0 [679] / gw1 [679] / gw2 [679]
    scheduling tests via LoadScheduling
    ............s..........................................................................................................................................................s..s...........................................................................................................................................................................................s.................................................................................................sssssssssssssssssss............................................................s................................................................s..............................................................................
    654 passed, 25 skipped in 47.25 seconds
    py35 runtests: commands[3] | python setup.py --quiet build_ext --inplace
    py35 runtests: commands[4] | python igor.py test_with_tracer c
    === CPython 3.5.2 with C tracer (.tox/py35/bin/python) ===
    gw0 [679] / gw1 [679] / gw2 [679]
    scheduling tests via LoadScheduling
    ...........s...............................................................................................................................................................................................s......s..........................................................................................................................................................s.................................................................................................s....................................................................................................................................s..................................................................................
    673 passed, 6 skipped in 53.20 seconds
    _________________________________________________________________________________________ summary __________________________________________________________________________________________
      py27: commands succeeded
      py35: commands succeeded

Tox runs the complete test suite twice for each version of Python you have
installed.  The first run uses the Python implementation of the trace function,
the second uses the C implementation.

To limit tox to just a few versions of Python, use the ``-e`` switch::

    $ tox -e py27,py33

To run just a few tests, you can use `pytest test selectors`_::

    $ tox tests/test_misc.py
    $ tox tests/test_misc.py::SetupPyTest
    $ tox tests/test_misc.py::SetupPyTest::test_metadata

These command run the tests in one file, one class, and just one test,
respectively.

Of course, run all the tests on every version of Python you have, before
submitting a change.

.. _pytest test selectors: http://doc.pytest.org/en/latest/usage.html#specifying-tests-selecting-tests


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


.. _Mercurial: https://www.mercurial-scm.org/
.. _tox: http://tox.testrun.org/
