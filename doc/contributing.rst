.. Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
.. For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

.. _contributing:

===========================
Contributing to coverage.py
===========================

.. highlight:: console

I welcome contributions to coverage.py.  Over the years, dozens of people have
provided patches of various sizes to add features or fix bugs.  This page
should have all the information you need to make a contribution.

One source of history or ideas are the `bug reports`_ against coverage.py.
There you can find ideas for requested features, or the remains of rejected
ideas.

.. _bug reports: https://github.com/nedbat/coveragepy/issues


Before you begin
----------------

If you have an idea for coverage.py, run it by me before you begin writing
code.  This way, I can get you going in the right direction, or point you to
previous work in the area.  Things are not always as straightforward as they
seem, and having the benefit of lessons learned by those before you can save
you frustration.


Getting the code
----------------

The coverage.py code is hosted on a GitHub repository at
https://github.com/nedbat/coveragepy.  To get a working environment, follow
these steps:

.. minimum of PYVERSIONS:

#.  Create a Python 3.7 virtualenv to work in, and activate it.

#.  Clone the repository::

    $ git clone https://github.com/nedbat/coveragepy
    $ cd coveragepy

#.  Install the requirements::

    $ pip install -r requirements/dev.pip

#.  Install a number of versions of Python.  Coverage.py supports a range
    of Python versions.  The more you can test with, the more easily your code
    can be used as-is.  If you only have one version, that's OK too, but may
    mean more work integrating your contribution.


Running the tests
-----------------

The tests are written mostly as standard unittest-style tests, and are run with
pytest running under `tox`_::

    $ tox
    py37 create: /Users/nedbat/coverage/trunk/.tox/py37
    py37 installdeps: -rrequirements/pip.pip, -rrequirements/pytest.pip, eventlet==0.25.1, greenlet==0.4.15
    py37 develop-inst: /Users/nedbat/coverage/trunk
    py37 installed: apipkg==1.5,appdirs==1.4.4,attrs==20.3.0,backports.functools-lru-cache==1.6.4,-e git+git@github.com:nedbat/coveragepy.git@36ef0e03c0439159c2245d38de70734fa08cddb4#egg=coverage,decorator==5.0.7,distlib==0.3.1,dnspython==2.1.0,eventlet==0.25.1,execnet==1.8.0,filelock==3.0.12,flaky==3.7.0,future==0.18.2,greenlet==0.4.15,hypothesis==6.10.1,importlib-metadata==4.0.1,iniconfig==1.1.1,monotonic==1.6,packaging==20.9,pluggy==0.13.1,py==1.10.0,PyContracts @ git+https://github.com/slorg1/contracts@c5a6da27d4dc9985f68e574d20d86000880919c3,pyparsing==2.4.7,pytest==6.2.3,pytest-forked==1.3.0,pytest-xdist==2.2.1,qualname==0.1.0,six==1.15.0,sortedcontainers==2.3.0,toml==0.10.2,typing-extensions==3.10.0.0,virtualenv==20.4.4,zipp==3.4.1
    py37 run-test-pre: PYTHONHASHSEED='376882681'
    py37 run-test: commands[0] | python setup.py --quiet clean develop
    py37 run-test: commands[1] | python igor.py zip_mods remove_extension
    py37 run-test: commands[2] | python igor.py test_with_tracer py
    === CPython 3.7.10 with Python tracer (.tox/py37/bin/python) ===
    bringing up nodes...
    ........................................................................................................................................................... [ 15%]
    ........................................................................................................................................................... [ 31%]
    ...........................................................................................................................................s............... [ 47%]
    ...........................................s...................................................................................sss.sssssssssssssssssss..... [ 63%]
    ........................................................................................................................................................s.. [ 79%]
    ......................................s..................................s................................................................................. [ 95%]
    ........................................ss......                                                                                                            [100%]
    949 passed, 29 skipped in 40.56s
    py37 run-test: commands[3] | python setup.py --quiet build_ext --inplace
    py37 run-test: commands[4] | python igor.py test_with_tracer c
    === CPython 3.7.10 with C tracer (.tox/py37/bin/python) ===
    bringing up nodes...
    ........................................................................................................................................................... [ 15%]
    ........................................................................................................................................................... [ 31%]
    ......................................................................s.................................................................................... [ 47%]
    ........................................................................................................................................................... [ 63%]
    ..........................s................................................s............................................................................... [ 79%]
    .................................................................................s......................................................................... [ 95%]
    ......................................s.........                                                                                                            [100%]
    973 passed, 5 skipped in 41.36s
    ____________________________________________________________________________ summary _____________________________________________________________________________
      py37: commands succeeded
      congratulations :)

Tox runs the complete test suite twice for each version of Python you have
installed.  The first run uses the Python implementation of the trace function,
the second uses the C implementation.

To limit tox to just a few versions of Python, use the ``-e`` switch::

    $ tox -e py37,py39

To run just a few tests, you can use `pytest test selectors`_::

    $ tox tests/test_misc.py
    $ tox tests/test_misc.py::HasherTest
    $ tox tests/test_misc.py::HasherTest::test_string_hashing

These command run the tests in one file, one class, and just one test,
respectively.

You can also affect the test runs with environment variables. Define any of
these as 1 to use them:

- ``COVERAGE_NO_PYTRACER=1`` disables the Python tracer if you only want to
  run the CTracer tests.

- ``COVERAGE_NO_CTRACER=1`` disables the C tracer if you only want to run the
  PyTracer tests.

- ``COVERAGE_ONE_TRACER=1`` will use only one tracer for each Python version.
  This will use the C tracer if it is available, or the Python tracer if not.

- ``COVERAGE_AST_DUMP=1`` will dump the AST tree as it is being used during
  code parsing.

There are other environment variables that affect tests.  I use `set_env.py`_
as a simple terminal interface to see and set them.

Of course, run all the tests on every version of Python you have, before
submitting a change.

.. _pytest test selectors: https://doc.pytest.org/en/stable/usage.html#specifying-which-tests-to-run


Lint, etc
---------

I try to keep the coverage.py source as clean as possible.  I use pylint to
alert me to possible problems::

    $ make lint

The source is pylint-clean, even if it's because there are pragmas quieting
some warnings.  Please try to keep it that way, but don't let pylint warnings
keep you from sending patches.  I can clean them up.

Lines should be kept to a 100-character maximum length.  I recommend an
`editorconfig.org`_ plugin for your editor of choice.

Other style questions are best answered by looking at the existing code.
Formatting of docstrings, comments, long lines, and so on, should match the
code that already exists.

Many people love `black`_, but I would prefer not to run it on coverage.py.


Continuous integration
----------------------

When you make a pull request, `GitHub actions`__ will run all of the tests and
quality checks on your changes.  If any fail, either fix them or ask for help.

__ https://github.com/nedbat/coveragepy/actions


Dependencies
------------

Coverage.py has no direct runtime dependencies, and I would like to keep it
that way.

It has many development dependencies.  These are specified generically in the
``requirements/*.in`` files.  The .in files should have no versions specified
in them.  The specific versions to use are pinned in ``requirements/*.pip``
files.  These are created by running ``make upgrade``.

.. minimum of PYVERSIONS:

It's important to use Python 3.7 to run ``make upgrade`` so that the pinned
versions will work on all of the Python versions currently supported by
coverage.py.

If for some reason we need to constrain a version of a dependency, the
constraint should be specified in the ``requirements/pins.pip`` file, with a
detailed reason for the pin.


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
probably fine.  A pull request on GitHub is great, but a simple diff or
patch works too.

All contributions are expected to include tests for new functionality and
fixes.  If you need help writing tests, please ask.


.. _editorconfig.org: http://editorconfig.org
.. _tox: https://tox.readthedocs.io/
.. _black: https://pypi.org/project/black/
.. _set_env.py: https://nedbatchelder.com/blog/201907/set_envpy.html
