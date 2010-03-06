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

Coverage.py is a tool for measuring code coverage of Python programs. It
monitors your program, noting which parts of the code have been executed, then
analyzes the source to identify code that could have been executed but was not.

Coverage measurement is typically used to gauge the effectiveness of tests. It
can show which parts of your product code are being exercised by tests, and
which are not.

The latest version is 3.3.1, released 6 March 2010.
It is supported on Python 2.3 through 3.1.


Quick start
-----------

Getting started is easy:

#.  Install coverage.py from the `coverage page on the Python Package Index`__,
    or by using "easy_install coverage".  You may need to install the
    python-dev support files, for example with "apt-get install python-dev".

#.  Use ``coverage run`` to execute your program and gather data:

    .. code-block:: console

        $ coverage run my_program.py arg1 arg2
        blah blah ..your program's output.. blah blah

#.  Use ``coverage report`` to report on the results:

    .. code-block:: console

        $ coverage report -m
        Name                      Stmts   Exec  Cover   Missing
        -------------------------------------------------------
        my_program                   20     16    80%   33-35, 39
        my_other_module              56     50    89%   17-23
        -------------------------------------------------------
        TOTAL                        76     66    87%

#.  For a nicer presentation, use ``coverage html`` to get annotated HTML
    listings detailing missed lines:

    .. code-block:: console

        $ coverage html

    Then visit htmlcov/index.html in your browser, to see a
    `report like this`__.

__ http://pypi.python.org/pypi/coverage
__ /code/coverage/sample_html/index.html


Using coverage.py
-----------------

There are a few different ways to use coverage.py.  The simplest is the
:ref:`command line <cmd>`, which lets you run your program and see the results.
If you need more control over how your project is measured, you can use the
:ref:`API <api>`.

Some test runners provide coverage integration to make it easy to use coverage
while running tests.  For example, `nose`_ has a `cover plug-in`_.

You can fine-tune coverage's view of your code by directing it to ignore parts
that you know aren't interesting.  See :ref:`Excluding Code <excluding>` for
details.

.. _nose:           http://somethingaboutorange.com/mrl/projects/nose
.. _cover plug-in:  http://somethingaboutorange.com/mrl/projects/nose/0.11.1/plugins/cover.html


History
-------

Coverage.py was originally written by `Gareth Rees`_.
Since 2004, `Ned Batchelder`_ has extended and maintained it with the help of
`many others`_.

.. _Gareth Rees:    http://garethrees.org/
.. _Ned Batchelder: http://nedbatchelder.com
.. _many others:    http://bitbucket.org/ned/coveragepy/src/tip/AUTHORS.txt


More information
----------------

.. toctree::
    :maxdepth: 1

    cmd
    config
    api
    excluding
    branch
    subprocess
    faq
    changes


.. How it works
.. .coverage file format
