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
:history: 20110213T081200, claim true 3.2 compatibility.
:history: 20110604T114800, update for 3.5b1
:history: 20110629T082300, update for 3.5
:history: 20110827T221800, update for 3.5.1b1
:history: 20110923T081800, update for 3.5.1
:history: 20120429T162100, updated for 3.5.2b1
:history: 20120503T233800, updated for 3.5.2
:history: 20120929T093500, updated for 3.5.3
:history: 20121117T094900, Change from easy_install to pip.
:history: 20121128T203700, Updated for 3.6b1.
:history: 20121223T180600, Updated for 3.6b2.
:history: 20121229T112300, Updated for 3.6b3.
:history: 20130105T174000, Updated for 3.6
:history: 20131005T210000, Updated for 3.7
:history: 20131212T213300, Updated for 3.7.1
:history: 20140924T073000, Updated for 4.0a1


Coverage.py is a tool for measuring code coverage of Python programs. It
monitors your program, noting which parts of the code have been executed, then
analyzes the source to identify code that could have been executed but was not.

Coverage measurement is typically used to gauge the effectiveness of tests. It
can show which parts of your code are being exercised by tests, and which are
not.

.. ifconfig:: not prerelease

    The latest version is coverage.py 3.7.1, released 13 December 2013.
    It is supported on Python versions 2.6 through 3.4, and PyPy 2.2.

.. ifconfig:: prerelease

    The latest version is coverage.py 4.0a1, released 27 September 2014.
    It is supported on Python versions 2.6 through 3.4, PyPy 2.2 through 2.4,
    and PyPy3 2.3 and 2.4.
    **This is a pre-release build.  The usual warnings about possible bugs apply.**
    The latest stable version is coverage.py 3.7.1, `described here`_.

.. _described here: http://nedbatchelder.com/code/coverage


Quick start
-----------

Getting started is easy:

#.  Install coverage.py from the `coverage page on the Python Package Index`_,
    or by using "pip install coverage".  For a few more details, see
    :ref:`install`.

#.  Use ``coverage run`` to run your program and gather data:

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

    .. ifconfig:: not prerelease

        Then visit htmlcov/index.html in your browser, to see a
        `report like this`_.

    .. ifconfig:: prerelease

        Then visit htmlcov/index.html in your browser, to see a
        `report like this one`_.

.. _coverage page on the Python Package Index: http://pypi.python.org/pypi/coverage
.. _report like this: /code/coverage/sample_html/index.html
.. _report like this one: /code/coverage/sample_html_beta/index.html


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
.. _cover plug-in:  https://nose.readthedocs.org/en/latest/plugins/cover.html


.. _contact:

Getting help
------------

If the :ref:`FAQ <faq>` doesn't answer your question, you can discuss
coverage.py or get help using it on the `Testing In Python`_ mailing list.

.. _Testing In Python: http://lists.idyll.org/listinfo/testing-in-python

Bug reports are gladly accepted at the `Bitbucket issue tracker`_.
Bitbucket also hosts the `code repository`_. There is a `mirrored repo`_ on
GitHub.

.. _Bitbucket issue tracker: http://bitbucket.org/ned/coveragepy/issues
.. _code repository: http://bitbucket.org/ned/coveragepy
.. _mirrored repo: https://github.com/nedbat/coveragepy

`I can be reached`_ in a number of ways. I'm happy to answer questions about
using coverage.py.

.. _I can be reached:  http://nedbatchelder.com/site/aboutned.html



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
    api
    contributing
    trouble
    faq
    changes


.. How it works
.. .coverage file format
