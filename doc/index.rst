===========
coverage.py
===========

:history: 20090524T134300, brand new docs.
:history: 20090613T164000, final touches for 3.0
:history: 20090618T195900, minor tweaks
:history: 20090707T205200, changes for 3.0.1
:history: 20090913T084400, new command line syntax


Coverage.py is a tool for measuring code coverage of Python programs. It
monitors your program, noting which parts of the code have been executed, then
analyzes the source to identify code that could have been executed but was not.

Coverage measurement is typically used to gauge the effectiveness of tests. It
can show which parts of your product code are being exercised by tests, and
which are not.

The latest version is 3.0.1, released 7 July 2009.  It is supported on Python
2.3 through 2.6.


Quick start
-----------

Getting started is easy:

#.  Install coverage.py from the
    `coverage page on the cheeseshop <http://pypi.python.org/pypi/coverage>`_,
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

        $ coverage html -i -d htmlcov

    Then visit htmlcov/index.html in your browser, to see a
    `report like this </code/coverage/sample_html/index.html>`_.


Using coverage.py
-----------------

There are a few different ways to use coverage.py.  The simplest is the
:ref:`command line <cmd>`, which lets you run your program and see the results.
If you need more control over how your project is measured, you can use the
:ref:`API <api>`.

Some test runners provide coverage integration to make it easy to use coverage
while running tests.  For example, `nose <http://somethingaboutorange.com/mrl/projects/nose>`_
has a `cover plug-in <http://somethingaboutorange.com/mrl/projects/nose/0.11.1/plugins/cover.html>`_.

You can fine-tune coverage's view of your code by directing it to ignore parts
that you know aren't interesting.  See :ref:`Excluding Code <excluding>` for
details.


History
-------

Coverage.py was originally written by `Gareth Rees <http://garethrees.org/>`_.
Ned Batchelder has maintained and extended it since 2004.



More information
----------------

.. toctree::
    :maxdepth: 1
    
    cmd
    api
    excluding
    faq
    changes


.. How it works
.. .coverage file format
