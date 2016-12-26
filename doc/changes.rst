.. Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
.. For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

.. _changes:

====================================
Major change history for coverage.py
====================================

.. :history: 20090524T134300, brand new docs.
.. :history: 20090613T164000, final touches for 3.0
.. :history: 20090706T205000, changes for 3.0.1
.. :history: 20091004T170700, changes for 3.1
.. :history: 20091128T072200, changes for 3.2
.. :history: 20091205T161525, 3.2 final
.. :history: 20100221T151900, changes for 3.3
.. :history: 20100306T181400, changes for 3.3.1
.. :history: 20100725T211700, updated for 3.4.
.. :history: 20100820T151500, updated for 3.4b1
.. :history: 20100906T133800, updated for 3.4b2
.. :history: 20100919T163400, updated for 3.4 release.
.. :history: 20110604T214100, updated for 3.5b1
.. :history: 20110629T082200, updated for 3.5
.. :history: 20110923T081600, updated for 3.5.1
.. :history: 20120429T162100, updated for 3.5.2b1
.. :history: 20120503T233700, updated for 3.5.2
.. :history: 20120929T093100, updated for 3.5.3
.. :history: 20121129T060100, updated for 3.6b1.
.. :history: 20121223T180600, updated for 3.6b2.
.. :history: 20130105T173500, updated for 3.6
.. :history: 20131005T205700, updated for 3.7
.. :history: 20131212T213100, updated for 3.7.1
.. :history: 20150124T134800, updated for 4.0a4
.. :history: 20150802T174700, updated for 4.0b1
.. :history: 20150822T092800, updated for 4.0b2
.. :history: 20150919T072700, updated for 4.0
.. :history: 20151013T103000, updated for 4.0.1
.. :history: 20151104T050900, updated for 4.0.2
.. :history: 20151124T065800, updated for 4.0.3
.. :history: 20160110T125800, updated for 4.1b1
.. :history: 20160510T125200, updated for 4.1b3
.. :history: 20160521T074300, updated for 4.1
.. :history: 20161226T153200, updated for 4.3


These are the major changes for coverage.py.  For a more complete change
history, see the `CHANGES.rst`_ file in the source tree.

.. _CHANGES.rst: http://bitbucket.org/ned/coveragepy/src/tip/CHANGES.rst

.. module:: coverage

.. _changes_43:

Version 4.3 --- 2016-12-27
--------------------------

Special thanks to **Loïc Dachary**, who took an extraordinary interest in
coverage.py and contributed a number of improvements in this release.

- The HTML report now supports a ``--skip-covered`` option like the other
  reporting commands.  Thanks, Loïc Dachary for the implementation, closing
  `issue 433`_.

- Subprocesses that are measured with `automatic subprocess measurement`_ used
  to read in any pre-existing data file.  This meant data would be incorrectly
  carried forward from run to run.  Now those files are not read, so each
  subprocess only writes its own data. Fixes `issue 510`_.

- Coverage.py wouldn't execute `sys.excepthook`_ when an exception happened in
  your program.  Now it does, thanks to Andrew Hoos.  Closes `issue 535`_.

.. _sys.excepthook: https://docs.python.org/3/library/sys.html#sys.excepthook

- The ``coverage combine`` command will now fail if there are no data files to
  combine. The combine changes in 4.2 meant that multiple combines could lose
  data, leaving you with an empty .coverage data file. Fixes issues
  `issue 525`_, `issue 412`_, `issue 516`_, and probably `issue 511`_.

- The branch coverage issues described in `issue 493`_, `issue 496`_, and
  `issue 502`_ are now fixed, thanks to Loïc Dachary.

- Options can now be read from a tox.ini file, if any. Like setup.cfg, sections
  are prefixed with "coverage:", so ``[run]`` options will be read from the
  ``[coverage:run]`` section of tox.ini. Implements part of `issue 519`_.
  Thanks, Stephen Finucane.

- Coverage.py can now search .pex files for source, just as it can .zip and
  .egg.  Thanks, Peter Ebden.

.. _issue 412: https://bitbucket.org/ned/coveragepy/issues/412/coverage-combine-should-error-if-no
.. _issue 433: https://bitbucket.org/ned/coveragepy/issues/433/coverage-html-does-not-suport-skip-covered
.. _issue 493: https://bitbucket.org/ned/coveragepy/issues/493/confusing-branching-failure
.. _issue 496: https://bitbucket.org/ned/coveragepy/issues/496/incorrect-coverage-with-branching-and
.. _issue 502: https://bitbucket.org/ned/coveragepy/issues/502/incorrect-coverage-report-with-cover
.. _issue 510: https://bitbucket.org/ned/coveragepy/issues/510/erase-still-needed-in-42
.. _issue 511: https://bitbucket.org/ned/coveragepy/issues/511/version-42-coverage-combine-empties
.. _issue 516: https://bitbucket.org/ned/coveragepy/issues/516/running-coverage-combine-twice-deletes-all
.. _issue 519: https://bitbucket.org/ned/coveragepy/issues/519/coverage-run-sections-in-toxini-or-as
.. _issue 525: https://bitbucket.org/ned/coveragepy/issues/525/coverage-combine-when-not-in-parallel-mode
.. _issue 535: https://bitbucket.org/ned/coveragepy/issues/535/sysexcepthook-is-not-called


.. _changes_42:

Version 4.2 --- 2016-07-26
--------------------------

Work from the PyCon 2016 Sprints!

- BACKWARD INCOMPATIBILITY: the ``coverage combine`` command now ignores an
  existing ``.coverage`` data file.  It used to include that file in its
  combining.  This caused confusing results, and extra tox "clean" steps.  If
  you want the old behavior, use the new ``coverage combine --append`` option.

- Since ``concurrency=multiprocessing`` uses subprocesses, options specified on
  the coverage.py command line will not be communicated down to them.  Only
  options in the configuration file will apply to the subprocesses.
  Previously, the options didn't apply to the subprocesses, but there was no
  indication.  Now it is an error to use ``--concurrency=multiprocessing`` and
  other run-affecting options on the command line.  This prevents
  failures like those reported in `issue 495`_.

- The ``concurrency`` option can now take multiple values, to support programs
  using multiprocessing and another library such as eventlet.  This is only
  possible in the configuration file, not from the command line. The
  configuration file is the only way for sub-processes to all run with the same
  options.  Fixes `issue 484`_.  Thanks to Josh Williams for prototyping.

- Using a ``concurrency`` setting of ``multiprocessing`` now implies
  ``--parallel`` so that the main program is measured similarly to the
  sub-processes.

- When using `automatic subprocess measurement`_, running coverage commands
  would create spurious data files.  This is now fixed, thanks to diagnosis and
  testing by Dan Riti.  Closes `issue 492`_.

- A new configuration option, ``report:sort``, controls what column of the
  text report is used to sort the rows.  Thanks to Dan Wandschneider, this
  closes `issue 199`_.

- The HTML report has a more-visible indicator for which column is being
  sorted.  Closes `issue 298`_, thanks to Josh Williams.

- Filtering the HTML report is now faster, thanks to Ville Skyttä.

- If the HTML report cannot find the source for a file, the message now
  suggests using the ``-i`` flag to allow the report to continue. Closes
  `issue 231`_, thanks, Nathan Land.

- When reports are ignoring errors, there's now a warning if a file cannot be
  parsed, rather than being silently ignored.  Closes `issue 396`_. Thanks,
  Matthew Boehm.

- A new option for ``coverage debug`` is available: ``coverage debug config``
  shows the current configuration.  Closes `issue 454`_, thanks to Matthew
  Boehm.

- Running coverage as a module (``python -m coverage``) no longer shows the
  program name as ``__main__.py``.  Fixes `issue 478`_.  Thanks, Scott Belden.

- The `test_helpers` module has been moved into a separate pip-installable
  package: `unittest-mixins`_.

.. _automatic subprocess measurement: http://coverage.readthedocs.io/en/latest/subprocess.html
.. _issue 199: https://bitbucket.org/ned/coveragepy/issues/199/add-a-way-to-sort-the-text-report
.. _issue 231: https://bitbucket.org/ned/coveragepy/issues/231/various-default-behavior-in-report-phase
.. _issue 298: https://bitbucket.org/ned/coveragepy/issues/298/show-in-html-report-that-the-columns-are
.. _issue 396: https://bitbucket.org/ned/coveragepy/issues/396/coverage-xml-shouldnt-bail-out-on-parse
.. _issue 454: https://bitbucket.org/ned/coveragepy/issues/454/coverage-debug-config-should-be
.. _issue 478: https://bitbucket.org/ned/coveragepy/issues/478/help-shows-silly-program-name-when-running
.. _issue 484: https://bitbucket.org/ned/coveragepy/issues/484/multiprocessing-greenlet-concurrency
.. _issue 492: https://bitbucket.org/ned/coveragepy/issues/492/subprocess-coverage-strange-detection-of
.. _issue 495: https://bitbucket.org/ned/coveragepy/issues/495/branch-and-concurrency-are-conflicting
.. _unittest-mixins: https://pypi.python.org/pypi/unittest-mixins


.. _changes_41:

Version 4.1 --- 2016-05-21
--------------------------

- Branch analysis has been rewritten: it used to be based on bytecode, but now
  uses AST analysis.  This has changed a number of things:

  - More code paths are now considered runnable, especially in
    ``try``/``except`` structures.  This may mean that coverage.py will
    identify more code paths as uncovered.  This could either raise or lower
    your overall coverage number.

  - Python 3.5's ``async`` and ``await`` keywords are properly supported,
    fixing `issue 434`_.

  - Missing branches reported with ``coverage report -m`` will now say
    ``->exit`` for missed branches to the exit of a function, rather than a
    negative number.  Fixes `issue 469`_.

  - Some long-standing branch coverage bugs were fixed:

    - `issue 129`_: functions with only a docstring for a body would
      incorrectly report a missing branch on the ``def`` line.

    - `issue 212`_: code in an ``except`` block could be incorrectly marked as
      a missing branch.

    - `issue 146`_: context managers (``with`` statements) in a loop or ``try``
      block could confuse the branch measurement, reporting incorrect partial
      branches.

    - `issue 422`_: in Python 3.5, an actual partial branch could be marked as
      complete.

    - During branch coverage of single-line callables like lambdas and
      generator expressions, coverage.py can now distinguish between them never
      being called, or being called but not completed.  Fixes `issue 90`_,
      `issue 460`_ and `issue 475`_.

- Pragmas to disable coverage measurement can now be used on decorator lines,
  and they will apply to the entire function or class being decorated.  This
  implements the feature requested in `issue 131`_.

- Multiprocessing support is now available on Windows.  Thanks, Rodrigue
  Cloutier.

- The HTML report has a few changes:

  - The HTML report now has a map of the file along the rightmost edge of the
    page, giving an overview of where the missed lines are.  Thanks, Dmitry
    Shishov.

  - The HTML report now uses different monospaced fonts, favoring Consolas over
    Courier.  Along the way, `issue 472`_ about not properly handling one-space
    indents was fixed.  The index page also has slightly different styling, to
    try to make the clickable detail pages more apparent.

- The XML report now produces correct package names for modules found in
  directories specified with ``source=``.  Fixes `issue 465`_.

- ``coverage --help`` and ``coverage --version`` now mention which tracer is
  installed, to help diagnose problems. The docs mention which features need
  the C extension. (`issue 479`_)

- The `Coverage.report` function had two parameters with non-None defaults,
  which have been changed.  `show_missing` used to default to True, but now
  defaults to None.  If you had been calling `Coverage.report` without
  specifying `show_missing`, you'll need to explicitly set it to True to keep
  the same behavior.  `skip_covered` used to default to False. It is now None,
  which doesn't change the behavior.  This fixes `issue 485`_.

- It's never been possible to pass a namespace module to one of the analysis
  functions, but now at least we raise a more specific error message, rather
  than getting confused. (`issue 456`_)

- The `coverage.process_startup` function now returns the `Coverage` instance
  it creates, as suggested in `issue 481`_.

.. _issue 90: https://bitbucket.org/ned/coveragepy/issues/90/lambda-expression-confuses-branch
.. _issue 129: https://bitbucket.org/ned/coveragepy/issues/129/misleading-branch-coverage-of-empty
.. _issue 131: https://bitbucket.org/ned/coveragepy/issues/131/pragma-on-a-decorator-line-should-affect
.. _issue 146: https://bitbucket.org/ned/coveragepy/issues/146/context-managers-confuse-branch-coverage
.. _issue 212: https://bitbucket.org/ned/coveragepy/issues/212/coverage-erroneously-reports-partial
.. _issue 422: https://bitbucket.org/ned/coveragepy/issues/422/python35-partial-branch-marked-as-fully
.. _issue 434: https://bitbucket.org/ned/coveragepy/issues/434/indexerror-in-python-35
.. _issue 456: https://bitbucket.org/ned/coveragepy/issues/456/coverage-breaks-with-implicit-namespaces
.. _issue 460: https://bitbucket.org/ned/coveragepy/issues/460/confusing-html-report-for-certain-partial
.. _issue 461: https://bitbucket.org/ned/coveragepy/issues/461/multiline-asserts-need-too-many-pragma
.. _issue 465: https://bitbucket.org/ned/coveragepy/issues/465/coveragexml-produces-package-names-with-an
.. _issue 469: https://bitbucket.org/ned/coveragepy/issues/469/strange-1-line-number-in-branch-coverage
.. _issue 472: https://bitbucket.org/ned/coveragepy/issues/472/html-report-indents-incorrectly-for-one
.. _issue 475: https://bitbucket.org/ned/coveragepy/issues/475/generator-expression-is-marked-as-not
.. _issue 479: https://bitbucket.org/ned/coveragepy/issues/479/clarify-the-need-for-the-c-extension
.. _issue 481: https://bitbucket.org/ned/coveragepy/issues/481/asyncioprocesspoolexecutor-tracing-not
.. _issue 485: https://bitbucket.org/ned/coveragepy/issues/485/coveragereport-ignores-show_missing-and


.. _changes_403:

Version 4.0.3 --- 2015-11-24
----------------------------

- Fixed a mysterious problem that manifested in different ways: sometimes
  hanging the process (`issue 420`_), sometimes making database connections
  fail (`issue 445`_).

- The XML report now has correct ``<source>`` elements when using a
  ``--source=`` option somewhere besides the current directory.  This fixes
  `issue 439`_. Thanks, Arcady Ivanov.

- Fixed an unusual edge case of detecting source encodings, described in
  `issue 443`_.

- Help messages that mention the command to use now properly use the actual
  command name, which might be different than "coverage".  Thanks to Ben
  Finney, this closes `issue 438`_.

.. _issue 420: https://bitbucket.org/ned/coveragepy/issues/420/coverage-40-hangs-indefinitely-on-python27
.. _issue 438: https://bitbucket.org/ned/coveragepy/issues/438/parameterise-coverage-command-name
.. _issue 439: https://bitbucket.org/ned/coveragepy/issues/439/incorrect-cobertura-file-sources-generated
.. _issue 443: https://bitbucket.org/ned/coveragepy/issues/443/coverage-gets-confused-when-encoding
.. _issue 445: https://bitbucket.org/ned/coveragepy/issues/445/django-app-cannot-connect-to-cassandra


.. _changes_402:

Version 4.0.2 --- 2015-11-04
----------------------------

- More work on supporting unusually encoded source. Fixed `issue 431`_.

- Files or directories with non-ASCII characters are now handled properly,
  fixing `issue 432`_.

- Setting a trace function with sys.settrace was broken by a change in 4.0.1,
  as reported in `issue 436`_.  This is now fixed.

- Officially support PyPy 4.0, which required no changes, just updates to the
  docs.

.. _issue 431: https://bitbucket.org/ned/coveragepy/issues/431/couldnt-parse-python-file-with-cp1252
.. _issue 432: https://bitbucket.org/ned/coveragepy/issues/432/path-with-unicode-characters-various
.. _issue 436: https://bitbucket.org/ned/coveragepy/issues/436/disabled-coverage-ctracer-may-rise-from


.. _changes_401:

Version 4.0.1 --- 2015-10-13
----------------------------

- When combining data files, unreadable files will now generate a warning
  instead of failing the command.  This is more in line with the older
  coverage.py v3.7.1 behavior, which silently ignored unreadable files.
  Prompted by `issue 418`_.

- The --skip-covered option would skip reporting on 100% covered files, but
  also skipped them when calculating total coverage.  This was wrong, it should
  only remove lines from the report, not change the final answer.  This is now
  fixed, closing `issue 423`_.

- In 4.0, the data file recorded a summary of the system on which it was run.
  Combined data files would keep all of those summaries.  This could lead to
  enormous data files consisting of mostly repetitive useless information. That
  summary is now gone, fixing `issue 415`_.  If you want summary information,
  get in touch, and we'll figure out a better way to do it.

- Test suites that mocked os.path.exists would experience strange failures, due
  to coverage.py using their mock inadvertently.  This is now fixed, closing
  `issue 416`_.

- Importing a ``__init__`` module explicitly would lead to an error:
  ``AttributeError: 'module' object has no attribute '__path__'``, as reported
  in `issue 410`_.  This is now fixed.

- Code that uses ``sys.settrace(sys.gettrace())`` used to incur a more than 2x
  speed penalty.  Now there's no penalty at all. Fixes `issue 397`_.

- Pyexpat C code will no longer be recorded as a source file, fixing
  `issue 419`_.

- The source kit now contains all of the files needed to have a complete source
  tree, re-fixing `issue 137`_ and closing `issue 281`_.

.. _issue 281: https://bitbucket.org/ned/coveragepy/issues/281/supply-scripts-for-testing-in-the
.. _issue 397: https://bitbucket.org/ned/coveragepy/issues/397/stopping-and-resuming-coverage-with
.. _issue 410: https://bitbucket.org/ned/coveragepy/issues/410/attributeerror-module-object-has-no
.. _issue 415: https://bitbucket.org/ned/coveragepy/issues/415/repeated-coveragedataupdates-cause
.. _issue 416: https://bitbucket.org/ned/coveragepy/issues/416/mocking-ospathexists-causes-failures
.. _issue 418: https://bitbucket.org/ned/coveragepy/issues/418/json-parse-error
.. _issue 419: https://bitbucket.org/ned/coveragepy/issues/419/nosource-no-source-for-code-path-to-c
.. _issue 423: https://bitbucket.org/ned/coveragepy/issues/423/skip_covered-changes-reported-total


.. _changes_40:

Version 4.0 --- 2015-09-20
--------------------------

Backward incompatibilities:

- Python versions supported are now:

  - CPython 2.6, 2.7, 3.3, 3.4 and 3.5
  - PyPy2 2.4, 2.6
  - PyPy3 2.4

- The original command line switches (``-x`` to run a program, etc) are no
  longer supported.

- The ``COVERAGE_OPTIONS`` environment variable is no longer supported.  It was
  a hack for ``--timid`` before configuration files were available.

- The original module-level function interface to coverage.py is no longer
  supported.  You must now create a :class:`coverage.Coverage` object, and use
  methods on it.

- The ``Coverage.use_cache`` method is no longer supported.

- The private method ``Coverage._harvest_data`` is now called
  :meth:`Coverage.get_data`, and returns the :class:`CoverageData` containing
  the collected data.

- Coverage.py is now licensed under the Apache 2.0 license. See `NOTICE.txt`_
  for details.

- Coverage.py kits no longer include tests and docs.  If you were using them,
  get in touch and let me know how.

.. _NOTICE.txt: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt


Major new features:

- Plugins: third parties can write plugins to add file support for non-Python
  files, such as web application templating engines, or languages that compile
  down to Python.  See :ref:`plugins` for how to use plugins, and
  :ref:`api_plugin` for details of how to write them.  A plugin for measuring
  Django template coverage is available: `django_coverage_plugin`_

- Gevent, eventlet, and greenlet are now supported.  The ``[run] concurrency``
  setting, or the ``--concurrency`` command line switch, specifies the
  concurrency library in use.  Huge thanks to Peter Portante for initial
  implementation, and to Joe Jevnik for the final insight that completed the
  work.

- The data storage has been re-written, using JSON instead of pickle.  The
  :class:`.CoverageData` class is a new supported API to the contents of the
  data file.  Data files from older versions of coverage.py can be converted to
  the new format with ``python -m coverage.pickle2json``.

- Wildly experimental: support for measuring processes started by the
  multiprocessing module.  To use, set ``--concurrency=multiprocessing``,
  either on the command line or in the .coveragerc file. Thanks, Eduardo
  Schettino.  Currently, this does not work on Windows.


New features:

- Options are now also read from a setup.cfg file, if any.  Sections are
  prefixed with "coverage:", so the ``[run]`` options will be read from the
  ``[coverage:run]`` section of setup.cfg.

- The HTML report now has filtering.  Type text into the Filter box on the
  index page, and only modules with that text in the name will be shown.
  Thanks, Danny Allen.

- A new option: ``coverage report --skip-covered``
  (or ``[report] skip_covered``) will reduce the number of files reported by
  skipping files with 100% coverage.  Thanks, Krystian Kichewko.  This means
  that empty ``__init__.py`` files will be skipped, since they are 100%
  covered.

- You can now specify the ``--fail-under`` option in the ``.coveragerc`` file
  as the ``[report] fail_under`` option.

- The ``report -m`` command now shows missing branches when reporting on branch
  coverage.  Thanks, Steve Leonard.

- The ``coverage combine`` command now accepts any number of directories or
  files as arguments, and will combine all the data from them.  This means you
  don't have to copy the files to one directory before combining.  Thanks,
  Christine Lytwynec.

- A new configuration option for the XML report: ``[xml] package_depth``
  controls which directories are identified as packages in the report.
  Directories deeper than this depth are not reported as packages.
  The default is that all directories are reported as packages.
  Thanks, Lex Berezhny.

- A new configuration option, ``[run] note``, lets you set a note that will be
  stored in the ``runs`` section of the data file.  You can use this to
  annotate the data file with any information you like.

- The COVERAGE_DEBUG environment variable can be used to set the
  ``[run] debug`` configuration option to control what internal operations are
  logged.

- A new version identifier is available, `coverage.version_info`, a plain tuple
  of values similar to `sys.version_info`_.


Improvements:

- Coverage.py now always adds the current directory to sys.path, so that
  plugins can import files in the current directory.

- Coverage.py now accepts a directory name for ``coverage run`` and will run a
  ``__main__.py`` found there, just like Python will.  Thanks, Dmitry Trofimov.

- The ``--debug`` switch can now be used on any command.

- Reports now use file names with extensions.  Previously, a report would
  describe a/b/c.py as "a/b/c".  Now it is shown as "a/b/c.py".  This allows
  for better support of non-Python files.

- Missing branches in the HTML report now have a bit more information in the
  right-hand annotations.  Hopefully this will make their meaning clearer.

- The XML report now contains a <source> element.  Thanks Stan Hu.

- The XML report now includes a ``missing-branches`` attribute.  Thanks, Steve
  Peak.  This is not a part of the Cobertura DTD, so the XML report no longer
  references the DTD.

- The XML report now reports each directory as a package again.  This was a bad
  regression, I apologize.

- In parallel mode, ``coverage erase`` will now delete all of the data files.

- A new warning is possible, if a desired file isn't measured because it was
  imported before coverage.py was started.

- The :func:`coverage.process_startup` function now will start coverage
  measurement only once, no matter how many times it is called.  This fixes
  problems due to unusual virtualenv configurations.

- Unrecognized configuration options will now print an error message and stop
  coverage.py.  This should help prevent configuration mistakes from passing
  silently.


API changes:

- The class defined in the coverage module is now called ``Coverage`` instead
  of ``coverage``, though the old name still works, for backward compatibility.

- You can now programmatically adjust the configuration of coverage.py by
  calling :meth:`Coverage.set_option` after construction.
  :meth:`Coverage.get_option` reads the configuration values.

- If the `config_file` argument to the Coverage constructor is specified as
  ".coveragerc", it is treated as if it were True.  This means setup.cfg is
  also examined, and a missing file is not considered an error.


Bug fixes:

- The textual report and the HTML report used to report partial branches
  differently for no good reason.  Now the text report's "missing branches"
  column is a "partial branches" column so that both reports show the same
  numbers.  This closes `issue 342`_.

- The ``fail-under`` value is now rounded the same as reported results,
  preventing paradoxical results, fixing `issue 284`_.

- Branch coverage couldn't properly handle certain extremely long files. This
  is now fixed, closing `issue 359`_.

- Branch coverage didn't understand yield statements properly.  Mickie Betz
  persisted in pursuing this despite Ned's pessimism.  Fixes `issue 308`_ and
  `issue 324`_.

- Files with incorrect encoding declaration comments are no longer ignored by
  the reporting commands.

- Empty files are now reported as 100% covered in the XML report, not 0%
  covered.

- The XML report will now create the output directory if need be. Thanks, Chris
  Rose.

- HTML reports no longer raise UnicodeDecodeError if a Python file has
  undecodable characters.

- The annotate command will now annotate all files, not just ones relative to
  the current directory.


.. _django_coverage_plugin: https://pypi.python.org/pypi/django_coverage_plugin
.. _issue 284: https://bitbucket.org/ned/coveragepy/issue/284/fail-under-should-show-more-precision
.. _issue 308: https://bitbucket.org/ned/coveragepy/issue/308/yield-lambda-branch-coverage
.. _issue 324: https://bitbucket.org/ned/coveragepy/issue/324/yield-in-loop-confuses-branch-coverage
.. _issue 342: https://bitbucket.org/ned/coveragepy/issue/342/console-and-html-coverage-reports-differ
.. _issue 359: https://bitbucket.org/ned/coveragepy/issue/359/xml-report-chunk-error
.. _sys.version_info: https://docs.python.org/3/library/sys.html#sys.version_info


.. _changes_371:

Version 3.7.1 --- 2013-12-13
----------------------------

- Improved the speed of HTML report generation by about 20%.

- Fixed the mechanism for finding OS-installed static files for the HTML report
  so that it will actually find OS-installed static files.


.. _changes_37:

Version 3.7 --- 2013-10-06
--------------------------

- Added the ``--debug`` switch to ``coverage run``.  It accepts a list of
  options indicating the type of internal activity to log to stderr. For
  details, see :ref:`the run --debug options <cmd_run_debug>`.

- Improved the branch coverage facility, fixing `issue 92`_ and `issue 175`_.

- Running code with ``coverage run -m`` now behaves more like Python does,
  setting sys.path properly, which fixes `issue 207`_ and `issue 242`_.

- Coverage.py can now run .pyc files directly, closing `issue 264`_.

- Coverage.py properly supports .pyw files, fixing `issue 261`_.

- Omitting files within a tree specified with the ``source`` option would
  cause them to be incorrectly marked as unexecuted, as described in
  `issue 218`_.  This is now fixed.

- When specifying paths to alias together during data combining, you can now
  specify relative paths, fixing `issue 267`_.

- Most file paths can now be specified with username expansion (``~/src``, or
  ``~build/src``, for example), and with environment variable expansion
  (``build/$BUILDNUM/src``).

- Trying to create an XML report with no files to report on, would cause a
  ZeroDivideError, but no longer does, fixing `issue 250`_.

- When running a threaded program under the Python tracer, coverage.py no
  longer issues a spurious warning about the trace function changing: "Trace
  function changed, measurement is likely wrong: None."  This fixes
  `issue 164`_.

- Static files necessary for HTML reports are found in system-installed places,
  to ease OS-level packaging of coverage.py.  Closes `issue 259`_.

- Source files with encoding declarations, but a blank first line, were not
  decoded properly.  Now they are.  Thanks, Roger Hu.

- The source kit now includes the ``__main__.py`` file in the root coverage
  directory, fixing `issue 255`_.

.. _issue 92: https://bitbucket.org/ned/coveragepy/issue/92/finally-clauses-arent-treated-properly-in
.. _issue 164: https://bitbucket.org/ned/coveragepy/issue/164/trace-function-changed-warning-when-using
.. _issue 175: https://bitbucket.org/ned/coveragepy/issue/175/branch-coverage-gets-confused-in-certain
.. _issue 207: https://bitbucket.org/ned/coveragepy/issue/207/run-m-cannot-find-module-or-package-in
.. _issue 242: https://bitbucket.org/ned/coveragepy/issue/242/running-a-two-level-package-doesnt-work
.. _issue 218: https://bitbucket.org/ned/coveragepy/issue/218/run-command-does-not-respect-the-omit-flag
.. _issue 250: https://bitbucket.org/ned/coveragepy/issue/250/uncaught-zerodivisionerror-when-generating
.. _issue 255: https://bitbucket.org/ned/coveragepy/issue/255/directory-level-__main__py-not-included-in
.. _issue 259: https://bitbucket.org/ned/coveragepy/issue/259/allow-use-of-system-installed-third-party
.. _issue 261: https://bitbucket.org/ned/coveragepy/issue/261/pyw-files-arent-reported-properly
.. _issue 264: https://bitbucket.org/ned/coveragepy/issue/264/coverage-wont-run-pyc-files
.. _issue 267: https://bitbucket.org/ned/coveragepy/issue/267/relative-path-aliases-dont-work


.. _changes_36:

Version 3.6 --- 2013-01-05
--------------------------

Features:

- The **report**, **html**, and **xml** commands now accept a ``--fail-under``
  switch that indicates in the exit status whether the coverage percentage was
  less than a particular value.  Closes `issue 139`_.

- The reporting functions coverage.report(), coverage.html_report(), and
  coverage.xml_report() now all return a float, the total percentage covered
  measurement.

- The HTML report's title can now be set in the configuration file, with the
  ``--title`` switch on the command line, or via the API.

- Configuration files now support substitution of environment variables, using
  syntax like ``${WORD}``.  Closes `issue 97`_.

Packaging:

- The C extension is optionally compiled using a different more widely-used
  technique, taking another stab at fixing `issue 80`_ once and for all.

- When installing, now in addition to creating a "coverage" command, two new
  aliases are also installed.  A "coverage2" or "coverage3" command will be
  created, depending on whether you are installing in Python 2.x or 3.x.
  A "coverage-X.Y" command will also be created corresponding to your specific
  version of Python.  Closes `issue 111`_.

- The coverage.py installer no longer tries to bootstrap setuptools or
  Distribute.  You must have one of them installed first, as `issue 202`_
  recommended.

- The coverage.py kit now includes docs (closing `issue 137`_) and tests.

Docs:

- Added a page to the docs about :doc:`contributing <contributing>` to
  coverage.py, closing `issue 171`_.

- Added a page to the docs about :doc:`troublesome situations <trouble>`,
  closing `issue 226`_.

- Docstrings for the legacy singleton methods are more helpful.  Thanks Marius
  Gedminas.  Closes `issue 205`_.

- The pydoc tool can now show documentation for the class `coverage.coverage`.
  Closes `issue 206`_.

- Added some info to the TODO file, closing `issue 227`_.

Fixes:

- Wildcards in ``include=`` and ``omit=`` arguments were not handled properly
  in reporting functions, though they were when running.  Now they are handled
  uniformly, closing `issue 143`_ and `issue 163`_.  **NOTE**: it is possible
  that your configurations may now be incorrect.  If you use ``include`` or
  ``omit`` during reporting, whether on the command line, through the API, or
  in a configuration file, please check carefully that you were not relying on
  the old broken behavior.

- Embarrassingly, the `[xml] output=` setting in the .coveragerc file simply
  didn't work.  Now it does.

- Combining data files would create entries for phantom files if used with
  ``source`` and path aliases.  It no longer does.

- ``debug sys`` now shows the configuration file path that was read.

- If an oddly-behaved package claims that code came from an empty-string
  file name, coverage.py no longer associates it with the directory name,
  fixing `issue 221`_.

- The XML report now consistently uses file names for the filename attribute,
  rather than sometimes using module names.  Fixes `issue 67`_.
  Thanks, Marcus Cobden.

- Coverage percentage metrics are now computed slightly differently under
  branch coverage.  This means that completely unexecuted files will now
  correctly have 0% coverage, fixing `issue 156`_.  This also means that your
  total coverage numbers will generally now be lower if you are measuring
  branch coverage.

- On Windows, files are now reported in their correct case, fixing `issue 89`_
  and `issue 203`_.

- If a file is missing during reporting, the path shown in the error message
  is now correct, rather than an incorrect path in the current directory.
  Fixes `issue 60`_.

- Running an HTML report in Python 3 in the same directory as an old Python 2
  HTML report would fail with a UnicodeDecodeError. This issue (`issue 193`_)
  is now fixed.

- Fixed yet another error trying to parse non-Python files as Python, this
  time an IndentationError, closing `issue 82`_ for the fourth time...

- If `coverage xml` fails because there is no data to report, it used to
  create a zero-length XML file.  Now it doesn't, fixing `issue 210`_.

- Jython files now work with the ``--source`` option, fixing `issue 100`_.

- Running coverage.py under a debugger is unlikely to work, but it shouldn't
  fail with "TypeError: 'NoneType' object is not iterable".  Fixes
  `issue 201`_.

- On some Linux distributions, when installed with the OS package manager,
  coverage.py would report its own code as part of the results.  Now it won't,
  fixing `issue 214`_, though this will take some time to be repackaged by the
  operating systems.

- When coverage.py ended unsuccessfully, it may have reported odd errors like
  ``'NoneType' object has no attribute 'isabs'``.  It no longer does,
  so kiss `issue 153`_ goodbye.


.. _issue 60: https://bitbucket.org/ned/coveragepy/issue/60/incorrect-path-to-orphaned-pyc-files
.. _issue 67: https://bitbucket.org/ned/coveragepy/issue/67/xml-report-filenames-may-be-generated
.. _issue 80: https://bitbucket.org/ned/coveragepy/issue/80/is-there-a-duck-typing-way-to-know-we-cant
.. _issue 89: https://bitbucket.org/ned/coveragepy/issue/89/on-windows-all-packages-are-reported-in
.. _issue 97: https://bitbucket.org/ned/coveragepy/issue/97/allow-environment-variables-to-be
.. _issue 100: https://bitbucket.org/ned/coveragepy/issue/100/source-directive-doesnt-work-for-packages
.. _issue 111: https://bitbucket.org/ned/coveragepy/issue/111/when-installing-coverage-with-pip-not
.. _issue 137: https://bitbucket.org/ned/coveragepy/issue/137/provide-docs-with-source-distribution
.. _issue 139: https://bitbucket.org/ned/coveragepy/issue/139/easy-check-for-a-certain-coverage-in-tests
.. _issue 143: https://bitbucket.org/ned/coveragepy/issue/143/omit-doesnt-seem-to-work-in-coverage
.. _issue 153: https://bitbucket.org/ned/coveragepy/issue/153/non-existent-filename-triggers
.. _issue 156: https://bitbucket.org/ned/coveragepy/issue/156/a-completely-unexecuted-file-shows-14
.. _issue 163: https://bitbucket.org/ned/coveragepy/issue/163/problem-with-include-and-omit-filename
.. _issue 171: https://bitbucket.org/ned/coveragepy/issue/171/how-to-contribute-and-run-tests
.. _issue 193: https://bitbucket.org/ned/coveragepy/issue/193/unicodedecodeerror-on-htmlpy
.. _issue 201: https://bitbucket.org/ned/coveragepy/issue/201/coverage-using-django-14-with-pydb-on
.. _issue 202: https://bitbucket.org/ned/coveragepy/issue/202/get-rid-of-ez_setuppy-and
.. _issue 203: https://bitbucket.org/ned/coveragepy/issue/203/duplicate-filenames-reported-when-filename
.. _issue 205: https://bitbucket.org/ned/coveragepy/issue/205/make-pydoc-coverage-more-friendly
.. _issue 206: https://bitbucket.org/ned/coveragepy/issue/206/pydoc-coveragecoverage-fails-with-an-error
.. _issue 210: https://bitbucket.org/ned/coveragepy/issue/210/if-theres-no-coverage-data-coverage-xml
.. _issue 214: https://bitbucket.org/ned/coveragepy/issue/214/coveragepy-measures-itself-on-precise
.. _issue 221: https://bitbucket.org/ned/coveragepy/issue/221/coveragepy-incompatible-with-pyratemp
.. _issue 226: https://bitbucket.org/ned/coveragepy/issue/226/make-readme-section-to-describe-when
.. _issue 227: https://bitbucket.org/ned/coveragepy/issue/227/update-todo


.. _changes_353:

Version 3.5.3 --- 2012-09-29
----------------------------

- Line numbers in the HTML report line up better with the source lines, fixing
  `issue 197`_, thanks Marius Gedminas.

- When specifying a directory as the source= option, the directory itself no
  longer needs to have a ``__init__.py`` file, though its sub-directories do,
  to be considered as source files.

- Files encoded as UTF-8 with a BOM are now properly handled, fixing
  `issue 179`_.  Thanks, Pablo Carballo.

- Fixed more cases of non-Python files being reported as Python source, and
  then not being able to parse them as Python.  Closes `issue 82`_ (again).
  Thanks, Julian Berman.

- Fixed memory leaks under Python 3, thanks, Brett Cannon. Closes `issue 147`_.

- Optimized .pyo files may not have been handled correctly, `issue 195`_.
  Thanks, Marius Gedminas.

- Certain unusually named file paths could have been mangled during reporting,
  `issue 194`_.  Thanks, Marius Gedminas.

- Try to do a better job of the impossible task of detecting when we can't
  build the C extension, fixing `issue 183`_.

.. _issue 147: https://bitbucket.org/ned/coveragepy/issue/147/massive-memory-usage-by-ctracer
.. _issue 179: https://bitbucket.org/ned/coveragepy/issue/179/htmlreporter-fails-when-source-file-is
.. _issue 183: https://bitbucket.org/ned/coveragepy/issue/183/install-fails-for-python-23
.. _issue 194: https://bitbucket.org/ned/coveragepy/issue/194/filelocatorrelative_filename-could-mangle
.. _issue 195: https://bitbucket.org/ned/coveragepy/issue/195/pyo-file-handling-in-codeunit
.. _issue 197: https://bitbucket.org/ned/coveragepy/issue/197/line-numbers-in-html-report-do-not-align


.. _changes_352:

Version 3.5.2 --- 2012-05-04
----------------------------

- The HTML report has slightly tweaked controls: the buttons at the top of
  the page are color-coded to the source lines they affect.

- Custom CSS can be applied to the HTML report by specifying a CSS file as
  the extra_css configuration value in the [html] section.

- Source files with custom encodings declared in a comment at the top are now
  properly handled during reporting on Python 2.  Python 3 always handled them
  properly.  This fixes `issue 157`_.

- Backup files left behind by editors are no longer collected by the source=
  option, fixing `issue 168`_.

- If a file doesn't parse properly as Python, we don't report it as an error
  if the file name seems like maybe it wasn't meant to be Python.  This is a
  pragmatic fix for `issue 82`_.

- The ``-m`` switch on ``coverage report``, which includes missing line numbers
  in the summary report, can now be specified as ``show_missing`` in the
  config file.  Closes `issue 173`_.

- When running a module with ``coverage run -m <modulename>``, certain details
  of the execution environment weren't the same as for
  ``python -m <modulename>``.  This had the unfortunate side-effect of making
  ``coverage run -m unittest discover`` not work if you had tests in a
  directory named "test".  This fixes `issue 155`_.

- Now the exit status of your product code is properly used as the process
  status when running ``python -m coverage run ...``.  Thanks, JT Olds.

- When installing into pypy, we no longer attempt (and fail) to compile
  the C tracer function, closing `issue 166`_.

.. _issue 82: https://bitbucket.org/ned/coveragepy/issue/82/tokenerror-when-generating-html-report
.. _issue 155: https://bitbucket.org/ned/coveragepy/issue/155/cant-use-coverage-run-m-unittest-discover
.. _issue 157: https://bitbucket.org/ned/coveragepy/issue/157/chokes-on-source-files-with-non-utf-8
.. _issue 166: https://bitbucket.org/ned/coveragepy/issue/166/dont-try-to-compile-c-extension-on-pypy
.. _issue 168: https://bitbucket.org/ned/coveragepy/issue/168/dont-be-alarmed-by-emacs-droppings
.. _issue 173: https://bitbucket.org/ned/coveragepy/issue/173/theres-no-way-to-specify-show-missing-in


.. _changes_351:

Version 3.5.1 --- 2011-09-23
----------------------------

- When combining data files from parallel runs, you can now instruct
  coverage.py about which directories are equivalent on different machines.  A
  ``[paths]`` section in the configuration file lists paths that are to be
  considered equivalent.  Finishes `issue 17`_.

- for-else constructs are understood better, and don't cause erroneous partial
  branch warnings.  Fixes `issue 122`_.

- Branch coverage for ``with`` statements is improved, fixing `issue 128`_.

- The number of partial branches reported on the HTML summary page was
  different than the number reported on the individual file pages.  This is
  now fixed.

- An explicit include directive to measure files in the Python installation
  wouldn't work because of the standard library exclusion.  Now the include
  directive takes precedence, and the files will be measured.  Fixes
  `issue 138`_.

- The HTML report now handles Unicode characters in Python source files
  properly.  This fixes `issue 124`_ and `issue 144`_. Thanks, Devin
  Jeanpierre.

- In order to help the core developers measure the test coverage of the
  standard library, Brandon Rhodes devised an aggressive hack to trick Python
  into running some coverage.py code before anything else in the process.
  See the coverage/fullcoverage directory if you are interested.

.. _issue 17: http://bitbucket.org/ned/coveragepy/issue/17/support-combining-coverage-data-from
.. _issue 122: http://bitbucket.org/ned/coveragepy/issue/122/for-else-always-reports-missing-branch
.. _issue 124: http://bitbucket.org/ned/coveragepy/issue/124/no-arbitrary-unicode-in-html-reports-in
.. _issue 128: http://bitbucket.org/ned/coveragepy/issue/128/branch-coverage-of-with-statement-in-27
.. _issue 138: http://bitbucket.org/ned/coveragepy/issue/138/include-should-take-precedence-over-is
.. _issue 144: http://bitbucket.org/ned/coveragepy/issue/144/failure-generating-html-output-for


.. _changes_35:

Version 3.5 --- 2011-06-29
--------------------------

HTML reporting:

- The HTML report now has hotkeys.  Try ``n``, ``s``, ``m``, ``x``, ``b``,
  ``p``, and ``c`` on the overview page to change the column sorting.
  On a file page, ``r``, ``m``, ``x``, and ``p`` toggle the run, missing,
  excluded, and partial line markings.  You can navigate the highlighted
  sections of code by using the ``j`` and ``k`` keys for next and previous.
  The ``1`` (one) key jumps to the first highlighted section in the file,
  and ``0`` (zero) scrolls to the top of the file.

- HTML reporting is now incremental: a record is kept of the data that
  produced the HTML reports, and only files whose data has changed will
  be generated.  This should make most HTML reporting faster.


Running Python files

- Modules can now be run directly using ``coverage run -m modulename``, to
  mirror Python's ``-m`` flag.  Closes `issue 95`_, thanks, Brandon Rhodes.

- ``coverage run`` didn't emulate Python accurately in one detail: the
  current directory inserted into ``sys.path`` was relative rather than
  absolute. This is now fixed.

- Pathological code execution could disable the trace function behind our
  backs, leading to incorrect code measurement.  Now if this happens,
  coverage.py will issue a warning, at least alerting you to the problem.
  Closes `issue 93`_.  Thanks to Marius Gedminas for the idea.

- The C-based trace function now behaves properly when saved and restored
  with ``sys.gettrace()`` and ``sys.settrace()``.  This fixes `issue 125`_
  and `issue 123`_.  Thanks, Devin Jeanpierre.

- Coverage.py can now be run directly from a working tree by specifying
  the directory name to python:  ``python coverage_py_working_dir run ...``.
  Thanks, Brett Cannon.

- A little bit of Jython support: `coverage run` can now measure Jython
  execution by adapting when $py.class files are traced. Thanks, Adi Roiban.


Reporting

- Partial branch warnings can now be pragma'd away.  The configuration option
  ``partial_branches`` is a list of regular expressions.  Lines matching any of
  those expressions will never be marked as a partial branch.  In addition,
  there's a built-in list of regular expressions marking statements which
  should never be marked as partial.  This list includes ``while True:``,
  ``while 1:``, ``if 1:``, and ``if 0:``.

- The ``--omit`` and ``--include`` switches now interpret their values more
  usefully.  If the value starts with a wildcard character, it is used as-is.
  If it does not, it is interpreted relative to the current directory.
  Closes `issue 121`_.

- Syntax errors in supposed Python files can now be ignored during reporting
  with the ``-i`` switch just like other source errors.  Closes `issue 115`_.

.. _issue 93: http://bitbucket.org/ned/coveragepy/issue/93/copying-a-mock-object-breaks-coverage
.. _issue 95: https://bitbucket.org/ned/coveragepy/issue/95/run-subcommand-should-take-a-module-name
.. _issue 115: https://bitbucket.org/ned/coveragepy/issue/115/fail-gracefully-when-reporting-on-file
.. _issue 121: https://bitbucket.org/ned/coveragepy/issue/121/filename-patterns-are-applied-stupidly
.. _issue 123: https://bitbucket.org/ned/coveragepy/issue/123/pyeval_settrace-used-in-way-that-breaks
.. _issue 125: https://bitbucket.org/ned/coveragepy/issue/125/coverage-removes-decoratortoolss-tracing


.. _changes_34:

Version 3.4 --- 2010-09-19
--------------------------

Controlling source:

- BACKWARD INCOMPATIBILITY: the ``--omit`` and ``--include`` switches now take
  file patterns rather than file prefixes, closing `issue 34`_ and `issue 36`_.

- BACKWARD INCOMPATIBILITY: the `omit_prefixes` argument is gone throughout
  coverage.py, replaced with `omit`, a list of file name patterns suitable for
  `fnmatch`.  A parallel argument `include` controls what files are included.

- The run command now has a ``--source`` switch, a list of directories or
  module names.  If provided, coverage.py will only measure execution in those
  source files.  The run command also now supports ``--include`` and ``--omit``
  to control what modules it measures.  This can speed execution and reduce the
  amount of data during reporting. Thanks Zooko.

- The reporting commands (report, annotate, html, and xml) now have an
  ``--include`` switch to restrict reporting to modules matching those file
  patterns, similar to the existing ``--omit`` switch. Thanks, Zooko.

Reporting:

- Completely unexecuted files can now be included in coverage results, reported
  as 0% covered.  This only happens if the --source option is specified, since
  coverage.py needs guidance about where to look for source files.

- Python files with no statements, for example, empty ``__init__.py`` files,
  are now reported as having zero statements instead of one.  Fixes `issue 1`_.

- Reports now have a column of missed line counts rather than executed line
  counts, since developers should focus on reducing the missed lines to zero,
  rather than increasing the executed lines to varying targets.  Once
  suggested, this seemed blindingly obvious.

- Coverage percentages are now displayed uniformly across reporting methods.
  Previously, different reports could round percentages differently.  Also,
  percentages are only reported as 0% or 100% if they are truly 0 or 100, and
  are rounded otherwise.  Fixes `issue 41`_ and `issue 70`_.

- The XML report output now properly includes a percentage for branch coverage,
  fixing `issue 65`_ and `issue 81`_, and the report is sorted by package
  name, fixing `issue 88`_.

- The XML report is now sorted by package name, fixing `issue 88`_.

- The precision of reported coverage percentages can be set with the
  ``[report] precision`` config file setting.  Completes `issue 16`_.

- Line numbers in HTML source pages are clickable, linking directly to that
  line, which is highlighted on arrival.  Added a link back to the index page
  at the bottom of each HTML page.

Execution and measurement:

- Various warnings are printed to stderr for problems encountered during data
  measurement: if a ``--source`` module has no Python source to measure, or is
  never encountered at all, or if no data is collected.

- Doctest text files are no longer recorded in the coverage data, since they
  can't be reported anyway.  Fixes `issue 52`_ and `issue 61`_.

- Threads derived from ``threading.Thread`` with an overridden `run` method
  would report no coverage for the `run` method.  This is now fixed, closing
  `issue 85`_.

- Programs that exited with ``sys.exit()`` with no argument weren't handled
  properly, producing a coverage.py stack trace.  This is now fixed.

- Programs that call ``os.fork`` will properly collect data from both the child
  and parent processes.  Use ``coverage run -p`` to get two data files that can
  be combined with ``coverage combine``.  Fixes `issue 56`_.

- When measuring code running in a virtualenv, most of the system library was
  being measured when it shouldn't have been.  This is now fixed.

- Coverage.py can now be run as a module: ``python -m coverage``.  Thanks,
  Brett Cannon.

.. _issue 1:  http://bitbucket.org/ned/coveragepy/issue/1/empty-__init__py-files-are-reported-as-1-executable
.. _issue 16: http://bitbucket.org/ned/coveragepy/issue/16/allow-configuration-of-accuracy-of-percentage-totals
.. _issue 34: http://bitbucket.org/ned/coveragepy/issue/34/enhanced-omit-globbing-handling
.. _issue 36: http://bitbucket.org/ned/coveragepy/issue/36/provide-regex-style-omit
.. _issue 41: http://bitbucket.org/ned/coveragepy/issue/41/report-says-100-when-it-isnt-quite-there
.. _issue 52: http://bitbucket.org/ned/coveragepy/issue/52/doctesttestfile-confuses-source-detection
.. _issue 56: http://bitbucket.org/ned/coveragepy/issue/56/coveragepy-cant-trace-child-processes-of-a
.. _issue 61: http://bitbucket.org/ned/coveragepy/issue/61/annotate-i-doesnt-work
.. _issue 65: http://bitbucket.org/ned/coveragepy/issue/65/branch-option-not-reported-in-cobertura
.. _issue 70: http://bitbucket.org/ned/coveragepy/issue/70/text-report-and-html-report-disagree-on-coverage
.. _issue 81: http://bitbucket.org/ned/coveragepy/issue/81/xml-report-does-not-have-condition-coverage-attribute-for-lines-with-a
.. _issue 85: http://bitbucket.org/ned/coveragepy/issue/85/threadrun-isnt-measured
.. _issue 88: http://bitbucket.org/ned/coveragepy/issue/88/xml-report-lists-packages-in-random-order


.. _changes_331:

Version 3.3.1 --- 2010-03-06
----------------------------

- Using ``parallel=True`` in a .coveragerc file prevented reporting, but now
  does not, fixing `issue 49`_.

- When running your code with ``coverage run``, if you call ``sys.exit()``,
  coverage.py will exit with that status code, fixing `issue 50`_.

.. _issue 49: http://bitbucket.org/ned/coveragepy/issue/49
.. _issue 50: http://bitbucket.org/ned/coveragepy/issue/50


.. _changes_33:

Version 3.3 --- 2010-02-24
--------------------------

- Settings are now read from a .coveragerc file.  A specific file can be
  specified on the command line with ``--rcfile=FILE``.  The name of the file
  can be programmatically set with the ``config_file`` argument to the
  coverage() constructor, or reading a config file can be disabled with
  ``config_file=False``.

- Added coverage.process_start to enable coverage measurement when Python
  starts.

- Parallel data file names now have a random number appended to them in
  addition to the machine name and process id. Also, parallel data files
  combined with ``coverage combine`` are deleted after they're combined, to
  clean up unneeded files. Fixes `issue 40`_.

- Exceptions thrown from product code run with ``coverage run`` are now
  displayed without internal coverage.py frames, so the output is the same as
  when the code is run without coverage.py.

- Fixed `issue 39`_ and `issue 47`_.

.. _issue 39: http://bitbucket.org/ned/coveragepy/issue/39
.. _issue 40: http://bitbucket.org/ned/coveragepy/issue/40
.. _issue 47: http://bitbucket.org/ned/coveragepy/issue/47


.. _changes_32:

Version 3.2 --- 2009-12-05
--------------------------

- Branch coverage: coverage.py can tell you which branches didn't have both (or
  all) choices executed, even where the choice doesn't affect which lines were
  executed.  See :ref:`branch` for more details.

- The table of contents in the HTML report is now sortable: click the headers
  on any column.  The sorting is persisted so that subsequent reports are
  sorted as you wish.  Thanks, `Chris Adams`_.

- XML reporting has file paths that let Cobertura find the source code, fixing
  `issue 21`_.

- The ``--omit`` option now works much better than before, fixing `issue 14`_
  and `issue 33`_.  Thanks, Danek Duvall.

- Added a ``--version`` option on the command line.

- Program execution under coverage.py is a few percent faster.

- Some exceptions reported by the command line interface have been cleaned up
  so that tracebacks inside coverage.py aren't shown.  Fixes `issue 23`_.

- Fixed some problems syntax coloring sources with line continuations and
  source with tabs: `issue 30`_ and `issue 31`_.

.. _Chris Adams: http://improbable.org/chris/
.. _issue 21: http://bitbucket.org/ned/coveragepy/issue/21
.. _issue 23: http://bitbucket.org/ned/coveragepy/issue/23
.. _issue 14: http://bitbucket.org/ned/coveragepy/issue/14
.. _issue 30: http://bitbucket.org/ned/coveragepy/issue/30
.. _issue 31: http://bitbucket.org/ned/coveragepy/issue/31
.. _issue 33: http://bitbucket.org/ned/coveragepy/issue/33


.. _changes_31:

Version 3.1 --- 2009-10-04
--------------------------

- Python 3.1 is now supported.

- Coverage.py has a new command line syntax with sub-commands.  This expands
  the possibilities for adding features and options in the future.  The old
  syntax is still supported.  Try ``coverage help`` to see the new commands.
  Thanks to Ben Finney for early help.

- Added an experimental ``coverage xml`` command for producing coverage reports
  in a Cobertura-compatible XML format.  Thanks, Bill Hart.

- Added the ``--timid`` option to enable a simpler slower trace function that
  works for DecoratorTools projects, including TurboGears.  Fixed `issue 12`_
  and `issue 13`_.

- HTML reports now display syntax-colored Python source.

- Added a ``coverage debug`` command for getting diagnostic information about
  the coverage.py installation.

- Source code can now be read from eggs.  Thanks, Ross Lawley.  Fixes
  `issue 25`_.

.. _issue 25: http://bitbucket.org/ned/coveragepy/issue/25
.. _issue 12: http://bitbucket.org/ned/coveragepy/issue/12
.. _issue 13: http://bitbucket.org/ned/coveragepy/issue/13


.. _changes_301:

Version 3.0.1 --- 2009-07-07
----------------------------

- Removed the recursion limit in the tracer function.  Previously, code that
  ran more than 500 frames deep would crash.

- Fixed a bizarre problem involving pyexpat, whereby lines following XML parser
  invocations could be overlooked.

- On Python 2.3, coverage.py could mis-measure code with exceptions being
  raised.  This is now fixed.

- The coverage.py code itself will now not be measured by coverage.py, and no
  coverage.py modules will be mentioned in the nose ``--with-cover`` plugin.

- When running source files, coverage.py now opens them in universal newline
  mode just like Python does.  This lets it run Windows files on Mac, for
  example.


.. _changes_30:

Version 3.0 --- 2009-06-13
--------------------------

- Coverage.py is now a package rather than a module.  Functionality has been
  split into classes.

- HTML reports and annotation of source files: use the new ``-b`` (browser)
  switch.  Thanks to George Song for code, inspiration and guidance.

- The trace function is implemented in C for speed.  Coverage.py runs are now
  much faster.  Thanks to David Christian for productive micro-sprints and
  other encouragement.

- The minimum supported Python version is 2.3.

- When using the object API (that is, constructing a coverage() object), data
  is no longer saved automatically on process exit.  You can re-enable it with
  the ``auto_data=True`` parameter on the coverage() constructor.
  The module-level interface still uses automatic saving.

- Code in the Python standard library is not measured by default.  If you need
  to measure standard library code, use the ``-L`` command-line switch during
  execution, or the ``cover_pylib=True`` argument to the coverage()
  constructor.

- API changes:

  - Added parameters to coverage.__init__ for options that had been set on
    the coverage object itself.

  - Added clear_exclude() and get_exclude_list() methods for programmatic
    manipulation of the exclude regexes.

  - Added coverage.load() to read previously-saved data from the data file.

  - coverage.annotate_file is no longer available.

  - Removed the undocumented cache_file argument to coverage.usecache().
