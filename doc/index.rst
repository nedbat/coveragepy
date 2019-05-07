.. Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
.. For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

===========
Coverage.py
===========

Coverage.py is a tool for measuring code coverage of Python programs. It
monitors your program, noting which parts of the code have been executed, then
analyzes the source to identify code that could have been executed but was not.

Coverage measurement is typically used to gauge the effectiveness of tests. It
can show which parts of your code are being exercised by tests, and which are
not.

.. ifconfig:: not prerelease

    The latest version is coverage.py 4.5.2, released November 12th 2018.  It
    is supported on:

    * Python versions 2.6, 2.7, 3.3, 3.4, 3.5, 3.6, 3.7, and pre-alpha 3.8.

    * PyPy2 6.0 and PyPy3 6.0.

    * Jython 2.7.1, though only for running code, not reporting.

    * IronPython 2.7.7, though only for running code, not reporting.

.. ifconfig:: prerelease

    The latest version is coverage.py 5.0a5, released May 7, 2019.
    It is supported on:

    * Python versions 2.7, 3.5, 3.6, 3.7, and alpha 3.8.

    * PyPy2 7.0 and PyPy3 7.0.

    * Jython 2.7.1, though only for running code, not reporting.

    * IronPython 2.7.7, though only for running code, not reporting.

    **This is a pre-release build.  The usual warnings about possible bugs
    apply.** The latest stable version is coverage.py 4.5.3, `described here`_.

.. _described here: http://coverage.readthedocs.io/

.. image:: media/Tidelift_Logos_RGB_Tidelift_Shorthand_On-White.png
   :width: 75
   :alt: Tidelift
   :align: left
   :class: tideliftlogo

Professional support for coverage.py is available as part of the `Tidelift
Subscription`_.  Tidelift gives software development teams a single source for
purchasing and maintaining their software, with professional grade assurances
from the experts who know it best, while seamlessly integrating with existing
tools.

.. _Tidelift Subscription: https://tidelift.com/subscription/pkg/pypi-coverage?utm_source=pypi-coverage&utm_medium=referral&utm_campaign=docs


Quick start
-----------

Getting started is easy:

#.  Install coverage.py from the `coverage.py page on the Python Package Index`_,
    or by using "pip install coverage".  For a few more details, see
    :ref:`install`.

#.  Use ``coverage run`` to run your program and gather data:

    .. code-block:: console

        # if you usually do:
        #
        #   $ python my_program.py arg1 arg2
        #
        # then instead do:

        $ coverage run my_program.py arg1 arg2
        blah blah ..your program's output.. blah blah

#.  Use ``coverage report`` to report on the results:

    .. code-block:: console

        $ coverage report -m
        Name                      Stmts   Miss  Cover   Missing
        -------------------------------------------------------
        my_program.py                20      4    80%   33-35, 39
        my_other_module.py           56      6    89%   17-23
        -------------------------------------------------------
        TOTAL                        76     10    87%

#.  For a nicer presentation, use ``coverage html`` to get annotated HTML
    listings detailing missed lines:

    .. code-block:: console

        $ coverage html

    .. ifconfig:: not prerelease

        Then open htmlcov/index.html in your browser, to see a
        `report like this`_.

    .. ifconfig:: prerelease

        Then open htmlcov/index.html in your browser, to see a
        `report like this one`_.

.. _coverage.py page on the Python Package Index: https://pypi.org/project/coverage/
.. _report like this: https://nedbatchelder.com/files/sample_coverage_html/index.html
.. _report like this one: https://nedbatchelder.com/files/sample_coverage_html_beta/index.html


Using coverage.py
-----------------

There are a few different ways to use coverage.py.  The simplest is the
:ref:`command line <cmd>`, which lets you run your program and see the results.
If you need more control over how your project is measured, you can use the
:ref:`API <api>`.

Some test runners provide coverage integration to make it easy to use
coverage.py while running tests.  For example, `pytest`_ has the `pytest-cov`_
plugin.

You can fine-tune coverage.py's view of your code by directing it to ignore
parts that you know aren't interesting.  See :ref:`source` and :ref:`excluding`
for details.

.. _pytest: http://doc.pytest.org
.. _pytest-cov: https://pytest-cov.readthedocs.io/


.. _contact:

Getting help
------------

If the :ref:`FAQ <faq>` doesn't answer your question, you can discuss
coverage.py or get help using it on the `Testing In Python`_ mailing list.

.. _Testing In Python: http://lists.idyll.org/listinfo/testing-in-python

Bug reports are gladly accepted at the `GitHub issue tracker`_.
GitHub also hosts the `code repository`_.

.. _GitHub issue tracker: https://github.com/nedbat/coveragepy/issues
.. _code repository: https://github.com/nedbat/coveragepy

Professional support for coverage.py is available as part of the `Tidelift
Subscription`_.

`I can be reached`_ in a number of ways. I'm happy to answer questions about
using coverage.py.

.. _I can be reached: https://nedbatchelder.com/site/aboutned.html



More information
----------------

.. toctree::
    :maxdepth: 1

    install
    cmd
    config
    source
    excluding
    branch
    subprocess
    contexts
    api
    howitworks
    plugins
    contributing
    trouble
    faq
    changes
