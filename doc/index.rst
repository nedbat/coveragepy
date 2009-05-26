===========
coverage.py
===========

:history: 20090524T134300, brand new docs.
:history: 20090524T134301, tweaked.

.. toctree::
    :hidden:

    cmd
    api


.. FAQ
..   Why do unexecutable lines show up as executed?
..   Why do the bodies of fns show as executed, but the def lines do not?
.. Change History
.. Getting Help
.. How it works
.. .coverage file format
.. Excluding lines

Coverage.py is a tool for measuring code coverage of Python programs. It monitors
your program, noting which parts of the code have been executed, then analyzes the
source to identify code that could have been executed but was not.


Quick Start
-----------

Getting started with coverage.py is easy:

#.  Install coverage.py from the
    `coverage page on the cheeseshop <http://pypi.python.org/pypi/coverage>`_.

#.  Run coverage.py to execute your program and gather data:

    .. code-block:: console

        $ coverage -e -x my_program.py arg1 arg2
        blah blah ..your program's output.. blah blah

#.  Run coverage.py to report on the results:

    .. code-block:: console

        $ coverage -r -m 
        Name                      Stmts   Exec  Cover   Missing
        -------------------------------------------------------
        my_program                   20     16    80%   33-35, 39
        my_other_module              56     50    89%   17-23
        -------------------------------------------------------
        TOTAL                        76     66    87%

#.  For a nicer presentation, run coverage.py to get annotated HTML listings
    detailing missed lines:
    
    .. code-block:: console

        $ coverage -b -i -d htmlcov

    Then visit htmlcov/index.html in your browser, to see a
    `report like this <sample_html/index.html>`_.

Getting Help
~~~~~~~~~~~~

This is a third-level section, with some XML:

.. code-block:: xml

    <tag attr='value'>1 &lt; 2 &amp 2 &gt; 1</tag>
    Whoa!


Using coverage.py
-----------------

There are two supported interfaces to coverage: a :ref:`command line <cmd>` and
an :ref:`API <api>`.
