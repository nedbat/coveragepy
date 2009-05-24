===========
coverage.py
===========

.. toctree::
    :hidden:

    cmd
    api


Coverage.py is a tool for measuring code coverage of Python programs. It monitors
your program, noting which parts of the code have been executed, then analyzes the
source to identify code that could have been executed but was not.


Quick Start
-----------

Install coverage.py from the cheeseshop.

Run coverage.py to execute your program and gather data::

    $ coverage -e -x my_program.py
    blah blah your program's output blah blah
    
Run coverage.py to report on the results::

    $ coverage -r -m 
    Name                      Stmts   Exec  Cover   Missing
    -------------------------------------------------------
    my_program                   20     16    80%   33-35, 39
    my_other_module              56     50    89%   517-523
    -------------------------------------------------------
    TOTAL                        76     66    87%

For a nicer presentation, run coverage.py to get annotated HTML listings
detailing missed lines::

    coverage -b -d htmlcov

Then visit htmlcov/index.html in your browser.


Using coverage.py
-----------------

There are two supported interfaces to coverage: a :ref:`command line <cmd>` and
an :ref:`API <api>`.
