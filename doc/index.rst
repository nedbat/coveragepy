===========
coverage.py
===========

:history: 20090524T134300, brand new docs.
:history: 20090613T164000, final touches for 3.0
:history: 20090618T195900, minor tweaks
:history: 20090707T205200, changes for 3.0.1
:history: 20090913T084400, new command line syntax
:history: 20091004T211900, version 3.1
:history: 20091127T155100, version 3.2
:history: 20091205T161429, version 3.2 for real.
:history: 20100224T204700, version 3.3
:history: 20100306T181500, version 3.3.1
:history: 20100725T211700, updated for 3.4.
:history: 20100820T151500, updated for 3.4b1.
:history: 20100906T134700, updated for 3.4b2.
:history: 20100919T163500, updated for 3.4 release.

Coverage.py is a tool for measuring code coverage of Python programs. It
monitors your program, noting which parts of the code have been executed, then
analyzes the source to identify code that could have been executed but was not.

Coverage measurement is typically used to gauge the effectiveness of tests. It
can show which parts of your code are being exercised by tests, and which are
not.

The latest version is 3.4, released 19 September 2010.
It is supported on Python 2.3 through 3.2 alpha 3.


Quick start
-----------

Getting started is easy:

#.  Install coverage.py from the `coverage page on the Python Package Index`_,
    or by using "easy_install coverage".  For a few more details, see
    :ref:`install`.

#.  Use ``coverage run`` to execute your program and gather data:

    .. code-block:: console

        $ coverage run my_program.py arg1 arg2
        blah blah ..your program's output.. blah blah

#.  Use ``coverage report`` to report on the results:

    .. code-block:: console

        $ coverage report -m
        Name                      Stmts   Miss  Cover   Missing
        -------------------------------------------------------
        my_program                   20      4    80%   33-35, 39
        my_other_module              56      6    89%   17-23
        -------------------------------------------------------
        TOTAL                        76     10    87%

#.  For a nicer presentation, use ``coverage html`` to get annotated HTML
    listings detailing missed lines:

    .. code-block:: console

        $ coverage html

    Then visit htmlcov/index.html in your browser, to see a
    `report like this`_.

.. _coverage page on the Python Package Index: http://pypi.python.org/pypi/coverage
.. _report like this: /code/coverage/sample_html/index.html


Using coverage.py
-----------------

There are a few different ways to use coverage.py.  The simplest is the
:ref:`command line <cmd>`, which lets you run your program and see the results.
If you need more control over how your project is measured, you can use the
:ref:`API <api>`.

Some test runners provide coverage integration to make it easy to use coverage
while running tests.  For example, `nose`_ has a `cover plug-in`_.

You can fine-tune coverage's view of your code by directing it to ignore parts
that you know aren't interesting.  See :ref:`source` and :ref:`excluding` for
details.

.. _nose:           http://somethingaboutorange.com/mrl/projects/nose
.. _cover plug-in:  http://somethingaboutorange.com/mrl/projects/nose/0.11.1/plugins/cover.html


History
-------

Coverage.py was originally written by `Gareth Rees`_.
Since 2004, `Ned Batchelder`_ has extended and maintained it with the help of
`many others`_.  The :ref:`change history <changes>` has all the details.

.. _Gareth Rees:    http://garethrees.org/
.. _Ned Batchelder: http://nedbatchelder.com
.. _many others:    http://bitbucket.org/ned/coveragepy/src/tip/AUTHORS.txt


More information
----------------

.. toctree::
    :maxdepth: 1

    install
    cmd
    config
    api
    source
    excluding
    branch
    subprocess
    faq
    changes


.. How it works
.. .coverage file format
