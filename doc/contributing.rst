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

#.  `Fork the repo`_ into your own GitHub account.  The coverage.py code will
    then be copied into a GitHub repository at
    ``https://github.com/GITHUB_USER/coveragepy`` where GITHUB_USER is your
    GitHub username.

#.  (Optional) Create a virtualenv to work in, and activate it.  There
    are a number of ways to do this.  Use the method you are comfortable with.

#.  Clone the repository::

    $ git clone https://github.com/GITHUB_USER/coveragepy
    $ cd coveragepy

#.  Install the requirements::

    $ python3 -m pip install -r requirements/dev.in

    Note: You may need to upgrade pip to install the requirements.


Running the tests
-----------------

The tests are written mostly as standard unittest-style tests, and are run with
pytest running under `tox`_::

    % python3 -m tox
    ROOT: tox-gh won't override envlist because tox is not running in GitHub Actions
    .pkg: _optional_hooks> python /usr/local/virtualenvs/coverage/lib/python3.7/site-packages/pyproject_api/_backend.py True setuptools.build_meta
    .pkg: get_requires_for_build_editable> python /usr/local/virtualenvs/coverage/lib/python3.7/site-packages/pyproject_api/_backend.py True setuptools.build_meta
    .pkg: build_editable> python /usr/local/virtualenvs/coverage/lib/python3.7/site-packages/pyproject_api/_backend.py True setuptools.build_meta
    py37: install_package> python -m pip install -U --force-reinstall --no-deps .tox/.tmp/package/87/coverage-7.2.3a0.dev1-0.editable-cp37-cp37m-macosx_10_15_x86_64.whl
    py37: commands[0]> python igor.py zip_mods
    py37: commands[1]> python setup.py --quiet build_ext --inplace
    py37: commands[2]> python -m pip install -q -e .
    py37: commands[3]> python igor.py test_with_tracer c
    === CPython 3.7.15 with C tracer (.tox/py37/bin/python) ===
    bringing up nodes...
    .........................................................................................................................x.................s....s....... [ 11%]
    ..s.....x.............................................s................................................................................................. [ 22%]
    ........................................................................................................................................................ [ 34%]
    ........................................................................................................................................................ [ 45%]
    ........................................................................................................................................................ [ 57%]
    .........s....................................................................................................................s......................... [ 68%]
    .................................s..............................s...............s..................................s.................................... [ 80%]
    ........................................................s............................................................................................... [ 91%]
    ......................................s.........................................................................                                         [100%]
    1316 passed, 12 skipped, 2 xfailed in 36.42s
    py37: commands[4]> python igor.py remove_extension
    py37: commands[5]> python igor.py test_with_tracer py
    === CPython 3.7.15 with Python tracer (.tox/py37/bin/python) ===
    bringing up nodes...
    ................................................................................................x...........................x.................s......... [ 11%]
    .....s.............s.s.....................................................s..............ss............................s.ss....ss.ss................... [ 22%]
    ......................................................................................................................................s................. [ 34%]
    ..................................................................................................................s..................................... [ 45%]
    ...................s.ss.....................................................................................s....................s.ss................... [ 57%]
    ..................s.s................................................................................................................................... [ 68%]
    ..........................s.........................................ssss...............s.................s...sss..................s...ss...ssss.s....... [ 80%]
    .......................................................................................................................................................s [ 91%]
    .........................................................................s.................................ss....                                        [100%]
    1281 passed, 47 skipped, 2 xfailed in 33.86s
    .pkg: _exit> python /usr/local/virtualenvs/coverage/lib/python3.7/site-packages/pyproject_api/_backend.py True setuptools.build_meta
      py37: OK (82.38=setup[2.80]+cmd[0.20,0.35,7.30,37.20,0.21,34.32] seconds)
      congratulations :) (83.61 seconds)

Tox runs the complete test suite twice for each version of Python you have
installed.  The first run uses the C implementation of the trace function,
the second uses the Python implementation.

To limit tox to just a few versions of Python, use the ``-e`` switch::

    $ python3 -m tox -e py37,py39

On the tox command line, options after ``--`` are passed to pytest.  To run
just a few tests, you can use `pytest test selectors`_::

    $ python3 -m tox -- tests/test_misc.py
    $ python3 -m tox -- tests/test_misc.py::HasherTest
    $ python3 -m tox -- tests/test_misc.py::HasherTest::test_string_hashing

These commands run the tests in one file, one class, and just one test,
respectively.  The pytest ``-k`` option selects tests based on a word in their
name, which can be very convenient for ad-hoc test selection.  Of course you
can combine tox and pytest options::

    $ python3 -m tox -q -e py37 -- -n 0 -vv -k hash
    === CPython 3.7.15 with C tracer (.tox/py37/bin/python) ===
    ======================================= test session starts ========================================
    platform darwin -- Python 3.7.15, pytest-7.2.2, pluggy-1.0.0 -- /Users/nedbat/coverage/.tox/py37/bin/python
    cachedir: .tox/py37/.pytest_cache
    rootdir: /Users/nedbat/coverage, configfile: setup.cfg
    plugins: flaky-3.7.0, hypothesis-6.70.0, xdist-3.2.1
    collected 1330 items / 1320 deselected / 10 selected
    run-last-failure: no previously failed tests, not deselecting items.

    tests/test_data.py::CoverageDataTest::test_add_to_hash_with_lines PASSED                     [ 10%]
    tests/test_data.py::CoverageDataTest::test_add_to_hash_with_arcs PASSED                      [ 20%]
    tests/test_data.py::CoverageDataTest::test_add_to_lines_hash_with_missing_file PASSED        [ 30%]
    tests/test_data.py::CoverageDataTest::test_add_to_arcs_hash_with_missing_file PASSED         [ 40%]
    tests/test_execfile.py::RunPycFileTest::test_running_hashed_pyc PASSED                       [ 50%]
    tests/test_misc.py::HasherTest::test_string_hashing PASSED                                   [ 60%]
    tests/test_misc.py::HasherTest::test_bytes_hashing PASSED                                    [ 70%]
    tests/test_misc.py::HasherTest::test_unicode_hashing PASSED                                  [ 80%]
    tests/test_misc.py::HasherTest::test_dict_hashing PASSED                                     [ 90%]
    tests/test_misc.py::HasherTest::test_dict_collision PASSED                                   [100%]

    =============================== 10 passed, 1320 deselected in 1.88s ================================
    Skipping tests with Python tracer: Only one tracer: no Python tracer for CPython
      py37: OK (12.22=setup[2.19]+cmd[0.20,0.36,6.57,2.51,0.20,0.19] seconds)
      congratulations :) (13.10 seconds)

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
`editorconfig.org`_ plugin for your editor of choice, which will also help with
indentation, line endings and so on.

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


.. _fork the repo: https://docs.github.com/en/get-started/quickstart/fork-a-repo
.. _editorconfig.org: http://editorconfig.org
.. _tox: https://tox.readthedocs.io/
.. _black: https://pypi.org/project/black/
.. _set_env.py: https://nedbatchelder.com/blog/201907/set_envpy.html
