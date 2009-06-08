===========
coverage.py
===========

:history: 20090524T134300, brand new docs.

Coverage.py is a tool for measuring code coverage of Python programs. It monitors
your program, noting which parts of the code have been executed, then analyzes the
source to identify code that could have been executed but was not.


Quick Start
-----------

Getting started with coverage.py is easy:

#.  Install coverage.py from the
    `coverage page on the cheeseshop <http://pypi.python.org/pypi/coverage>`_,
    or by using "easy_install coverage".  You may need to install the python-dev
    support files, for example with "apt-get install python-dev".

#.  Run coverage to execute your program and gather data:

    .. code-block:: console

        $ coverage -e -x my_program.py arg1 arg2
        blah blah ..your program's output.. blah blah

#.  Run coverage to report on the results:

    .. code-block:: console

        $ coverage -r -m 
        Name                      Stmts   Exec  Cover   Missing
        -------------------------------------------------------
        my_program                   20     16    80%   33-35, 39
        my_other_module              56     50    89%   17-23
        -------------------------------------------------------
        TOTAL                        76     66    87%

#.  For a nicer presentation, run coverage to get annotated HTML listings
    detailing missed lines:
    
    .. code-block:: console

        $ coverage -b -i -d htmlcov

    Then visit htmlcov/index.html in your browser, to see a
    `report like this </code/coverage/sample_html/index.html>`_.


Using coverage
--------------

There are a few different ways to use coverage.  The simplest is the
:ref:`command line <cmd>`, which lets you run your program and see the results.
If you need more control over how your project is measured, you can use the
:ref:`API <api>`.

Some test runners provide coverage integration to make it easy to use coverage
while running tests.  For example, `nose <http://somethingaboutorange.com/mrl/projects/nose>`
has a `cover plug-in <http://somethingaboutorange.com/mrl/projects/nose/0.11.1/plugins/cover.html>`_.


More information
----------------

.. toctree::
    :maxdepth: 1
    
    cmd
    api
    changes


.. FAQ
..   Why do unexecutable lines show up as executed?
..   Why do the bodies of fns show as executed, but the def lines do not?
.. Change History
.. Getting Help
.. How it works
.. .coverage file format
.. Excluding lines
