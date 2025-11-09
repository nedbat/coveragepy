.. Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
.. For details: https://github.com/coveragepy/coveragepy/blob/main/NOTICE.txt

.. Command samples here were made with a 100-column terminal.

.. _contributing:

===========================
Contributing to coverage.py
===========================

.. highlight:: console

I welcome contributions to coverage.py.  Over the years, hundreds of people
have provided contributions of various sizes to add features, fix bugs, or just
help diagnose thorny issues.  This page should have all the information you
need to make a contribution.

One source of history or ideas are the `bug reports`_ against coverage.py.
There you can find ideas for requested features, or the remains of rejected
ideas.

.. _bug reports: https://github.com/coveragepy/coveragepy/issues


Before you begin
----------------

If you have an idea for coverage.py, run it by me before you begin writing
code.  This way, I can get you going in the right direction, or point you to
previous work in the area.  Things are not always as straightforward as they
seem, and having the benefit of lessons learned by those before you can save
you frustration.

We have a `#coverage channel in the Python Discord <discord_>`_ that can be a
good place to explore ideas, get help, or help people with coverage.py.
`Join us <discord_>`_!

.. _discord: https://discord.com/channels/267624335836053506/1253355750684753950


Getting the code
----------------

.. PYVERSIONS (mention of lowest version in the "create virtualenv" step).

The coverage.py code is hosted on a GitHub repository at
https://github.com/coveragepy/coveragepy.  To get a working environment, follow
these steps:

#.  `Fork the repo`_ into your own GitHub account.  The coverage.py code will
    then be copied into a GitHub repository at
    ``https://github.com/GITHUB_USER/coveragepy`` where GITHUB_USER is your
    GitHub username.

#.  (Optional) Create a virtualenv to work in, and activate it.  There
    are a number of ways to do this.  Use the method you are comfortable with.
    Ideally, use Python 3.10 (the lowest version coverage.py supports).

#.  Clone the repository::

    $ git clone https://github.com/GITHUB_USER/coveragepy
    $ cd coveragepy

#.  Install the requirements with either of these commands::

    $ make install
    $ python3 -m pip install -r requirements/dev.pip

    Note: You may need to upgrade pip to install the requirements.


Running the tests
-----------------

.. To get the test output:
    # Use the lowest of the PYVERSIONS
    # Resize terminal width to 95
    % make sterile

.. with COVERAGE_ONE_CORE=

The tests are written mostly as standard unittest-style tests, and are run with
pytest running under `tox`_::

    % python3 -m tox -e py39
    py39: wheel-0.45.1-py3-none-any.whl already present in /Users/ned/Library/Application Support/virtualenv/wheel/3.9/embed/3/wheel.json
    py39: pip-25.0.1-py3-none-any.whl already present in /Users/ned/Library/Application Support/virtualenv/wheel/3.9/embed/3/pip.json
    py39: setuptools-78.1.0-py3-none-any.whl already present in /Users/ned/Library/Application Support/virtualenv/wheel/3.9/embed/3/setuptools.json
    py39: install_deps> python -m pip install -U -r requirements/pip.pip -r requirements/pytest.pip -r requirements/light-threads.pip
    .pkg: install_requires> python -I -m pip install setuptools
    .pkg: _optional_hooks> python /usr/local/virtualenvs/coverage/lib/python3.9/site-packages/pyproject_api/_backend.py True setuptools.build_meta
    .pkg: get_requires_for_build_editable> python /usr/local/virtualenvs/coverage/lib/python3.9/site-packages/pyproject_api/_backend.py True setuptools.build_meta
    .pkg: build_editable> python /usr/local/virtualenvs/coverage/lib/python3.9/site-packages/pyproject_api/_backend.py True setuptools.build_meta
    py39: install_package_deps> python -m pip install -U 'tomli; python_full_version <= "3.11.0a6"'
    py39: install_package> python -m pip install -U --force-reinstall --no-deps .tox/.tmp/package/1/coverage-7.8.1a0.dev1-0.editable-cp39-cp39-macosx_15_0_arm64.whl
    py39: commands[0]> python igor.py zip_mods
    py39: commands[1]> python igor.py remove_extension
    py39: commands[2]> python igor.py test_with_core pytrace
    === CPython 3.9.21 (gil) with Python tracer (.tox/py39/bin/python) ===
    bringing up nodes...
    ....................................................................................... [  5%]
    ..................................................................x................s... [ 11%]
    ......s...s.....s....s......s.s.s.s.................................................... [ 17%]
    ...........................................s..ss...ss.ss.ss............................ [ 23%]
    ....................................................................................... [ 29%]
    ....................................................................................... [ 35%]
    ....................................................................................... [ 41%]
    ................................................s...................................... [ 47%]
    ....................................................................................... [ 53%]
    ...................................................s..........s........................ [ 59%]
    ....................................................................................... [ 65%]
    ..........................ssss......................................................... [ 71%]
    ..s.....s.ss..........................ss...................s.s..sssssss.ssssss.sssss... [ 77%]
    .........ss..........................s...s.s......s........s........................s.. [ 83%]
    .............................s......................................................... [ 88%]
    ....................................................................................... [ 94%]
    .............................................s.......................ss....             [100%]
    1403 passed, 63 skipped, 1 xfailed in 15.05s
    py39: commands[3]> python setup.py --quiet build_ext --inplace
    py39: commands[4]> python -m pip install -q -e .
    py39: commands[5]> python igor.py test_with_core ctrace
    === CPython 3.9.21 (gil) with C tracer (.tox/py39/bin/python) ===
    bringing up nodes...
    ....................................................................................... [  5%]
    ..........................................sx................................s.......... [ 11%]
    ..........ss........s....................................s............................. [ 17%]
    ..............................sss...................................................... [ 23%]
    ..............................................................s........................ [ 29%]
    ....................................................................................... [ 35%]
    ....................................................................................... [ 41%]
    ......................................................s................................ [ 47%]
    .............................................s......................................... [ 53%]
    .......s..................s............................................................ [ 59%]
    ....................................................................................s.. [ 65%]
    .......................................................ss.......................s...... [ 71%]
    ....................................................s............................ss.... [ 77%]
    ..........................s...................s........................................ [ 83%]
    ....................................................................................... [ 88%]
    ............................s......s................................................... [ 94%]
    .................................................................s.........             [100%]
    1440 passed, 26 skipped, 1 xfailed in 12.38s
    py39: OK (40.04=setup[9.03]+cmd[0.17,0.09,15.40,0.13,2.47,12.77] seconds)
    congratulations :) (40.61 seconds)

Tox runs the complete test suite a few times for each version of Python you
have installed.  The first run uses the C implementation of the trace function,
the second uses the Python implementation.  If `sys.monitoring`_ is available,
the suite will be run again with that core.

To limit tox to just a few versions of Python, use the ``-e`` switch::

    $ python3 -m tox -e py38,py39

On the tox command line, options after ``--`` are passed to pytest.  To run
just a few tests, you can use `pytest test selectors`_::

    $ python3 -m tox -- tests/test_misc.py
    $ python3 -m tox -- tests/test_misc.py::HasherTest
    $ python3 -m tox -- tests/test_misc.py::HasherTest::test_string_hashing

.. with COVERAGE_ONE_CORE=1

These commands run the tests in one file, one class, and just one test,
respectively.  The pytest ``-k`` option selects tests based on a word in their
name, which can be very convenient for ad-hoc test selection.  Of course you
can combine tox and pytest options::

    % python3 -m tox -q -e py310 -- -n 0 -vv -k hash
    Skipping tests with Python tracer: Only one core: not running pytrace
    === CPython 3.10.16 (gil) with C tracer (.tox/py310/bin/python) ===
    ===================================== test session starts =====================================
    platform darwin -- Python 3.10.16, pytest-8.3.5, pluggy-1.5.0 -- /Users/ned/coverage/trunk/.tox/py310/bin/python
    cachedir: .tox/py310/.pytest_cache
    hypothesis profile 'default' -> database=DirectoryBasedExampleDatabase(PosixPath('/Users/ned/coverage/trunk/.hypothesis/examples'))
    rootdir: /Users/ned/coverage/trunk
    configfile: pyproject.toml
    plugins: flaky-3.8.1, hypothesis-6.128.1, xdist-3.6.1
    collected 1467 items / 1457 deselected / 10 selected
    run-last-failure: no previously failed tests, not deselecting items.

    tests/test_data.py::CoverageDataTest::test_add_to_hash_with_lines PASSED                [ 10%]
    tests/test_data.py::CoverageDataTest::test_add_to_hash_with_arcs PASSED                 [ 20%]
    tests/test_data.py::CoverageDataTest::test_add_to_lines_hash_with_missing_file PASSED   [ 30%]
    tests/test_data.py::CoverageDataTest::test_add_to_arcs_hash_with_missing_file PASSED    [ 40%]
    tests/test_execfile.py::RunPycFileTest::test_running_hashed_pyc PASSED                  [ 50%]
    tests/test_misc.py::HasherTest::test_string_hashing PASSED                              [ 60%]
    tests/test_misc.py::HasherTest::test_bytes_hashing PASSED                               [ 70%]
    tests/test_misc.py::HasherTest::test_unicode_hashing PASSED                             [ 80%]
    tests/test_misc.py::HasherTest::test_dict_hashing PASSED                                [ 90%]
    tests/test_misc.py::HasherTest::test_dict_collision PASSED                              [100%]

    ============================= 10 passed, 1457 deselected in 3.13s =============================
    py310: OK (16.62 seconds)
    congratulations :) (16.97 seconds)

You can also affect the test runs with environment variables:

- ``COVERAGE_ONE_CORE=1`` will use only one tracing core for each Python
  version.  This isn't about CPU cores, it's about the central code that tracks
  execution.  This will use the preferred core for the Python version and
  implementation being tested.

- ``COVERAGE_TEST_CORES=...`` defines the cores to run tests on.  Three cores
  are available, specify them as a comma-separated string:

  - ``ctrace`` is a sys.settrace function implemented in C.
  - ``pytrace`` is a sys.settrace function implemented in Python.
  - ``sysmon`` is a `sys.monitoring`_ implementation.

- ``COVERAGE_AST_DUMP=1`` will dump the AST tree as it is being used during
  code parsing.

There are other environment variables that affect tests.  I use `set_env.py`_
as a simple terminal interface to see and set them.

Of course, run all the tests on every version of Python you have before
submitting a change.


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
indentation, line endings and so on.  Source files are formatted with `ruff`_.

I use `pre-commit`_ to run checks and formatting when making commits, you
should also.

Other style questions are best answered by looking at the existing code.
Formatting of docstrings, comments, long lines, and so on, should match the
code that already exists.


Cog
---

Parts of the documentation and GitHub actions are kept up-to-date with `cog`_.
There are checks to make sure that files are correct and not being incorrectly
edited.

If a check fails, it will show you what command to run to update the files.
If you edit parts of a file that should be generated, you will see a message
like::

    Output has been edited! Delete old checksum to unprotect.

Probably you should revert the edits and run the command to generate the
output.  The top of the file you edited will have instructions.

.. _cog: https://cog.readthedocs.io


Continuous integration
----------------------

When you make a pull request, `GitHub actions`__ will run all of the tests and
quality checks on your changes.  If any fail, either fix them or ask for help.

__ https://github.com/coveragepy/coveragepy/actions


Dependencies
------------

Coverage.py has no direct runtime dependencies, and I would like to keep it
that way.

It has many development dependencies.  These are specified generically in the
``requirements/*.in`` files.  The .in files should have no versions specified
in them.  The specific versions to use are pinned in ``requirements/*.pip``
files.  These are created by running ``make upgrade``.

.. minimum of PYVERSIONS:

It's important to use Python 3.10 to run ``make upgrade`` so that the pinned
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
.. _ruff: https://pypi.org/project/ruff/
.. _pre-commit: https://pre-commit.com/
.. _set_env.py: https://nedbatchelder.com/blog/201907/set_envpy.html
.. _pytest test selectors: https://doc.pytest.org/en/stable/usage.html#specifying-which-tests-to-run
.. _sys.monitoring: https://docs.python.org/3/library/sys.monitoring.html
