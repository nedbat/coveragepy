.. Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
.. For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

==============================
Change history for coverage.py
==============================

These changes are listed in decreasing version number order. Note this can be
different from a strict chronological order when there are two branches in
development at the same time, such as 4.5.x and 5.0.

This list is detailed and covers changes in each pre-release version.

    .. When updating the "Unreleased" header to a specific version, use this
    .. format.  Don't forget the jump target:
    ..
    ..  .. _changes_981:
    ..
    ..  Version 9.8.1 — 2027-07-27
    ..  --------------------------

.. _changes_62:

Version 6.2 — 2021-11-26
------------------------

- Feature: Now the ``--concurrency`` setting can now have a list of values, so
  that threads and another lightweight threading package can be measured
  together, such as ``--concurrency=gevent,thread``.  Closes `issue 1012`_ and
  `issue 1082`_.

- Fix: A module specified as the ``source`` setting is imported during startup,
  before the user program imports it.  This could cause problems if the rest of
  the program isn't ready yet.  For example, `issue 1203`_ describes a Django
  setting that is accessed before settings have been configured.  Now the early
  import is wrapped in a try/except so errors then don't stop execution.

- Fix: A colon in a decorator expression would cause an exclusion to end too
  early, preventing the exclusion of the decorated function. This is now fixed.

- Fix: The HTML report now will not overwrite a .gitignore file that already
  exists in the HTML output directory (follow-on for `issue 1244`_).

- API: The exceptions raised by Coverage.py have been specialized, to provide
  finer-grained catching of exceptions by third-party code.

- API: Using ``suffix=False`` when constructing a Coverage object with
  multiprocessing wouldn't suppress the data file suffix (`issue 989`_).  This
  is now fixed.

- Debug: The `coverage debug data` command will now sniff out combinable data
  files, and report on all of them.

- Debug: The `coverage debug` command used to accept a number of topics at a
  time, and show all of them, though this was never documented.  This no longer
  works, to allow for command-line options in the future.

.. _issue 989: https://github.com/nedbat/coveragepy/issues/989
.. _issue 1012: https://github.com/nedbat/coveragepy/issues/1012
.. _issue 1082: https://github.com/nedbat/coveragepy/issues/1802
.. _issue 1203: https://github.com/nedbat/coveragepy/issues/1203


.. _changes_612:

Version 6.1.2 — 2021-11-10
--------------------------

- Python 3.11 is supported (tested with 3.11.0a2).  One still-open issue has to
  do with `exits through with-statements <issue 1270_>`_.

- Fix: When remapping file paths through the ``[paths]`` setting while
  combining, the ``[run] relative_files`` setting was ignored, resulting in
  absolute paths for remapped file names (`issue 1147`_).  This is now fixed.

- Fix: Complex conditionals over excluded lines could have incorrectly reported
  a missing branch (`issue 1271`_). This is now fixed.

- Fix: More exceptions are now handled when trying to parse source files for
  reporting.  Problems that used to terminate coverage.py can now be handled
  with ``[report] ignore_errors``.  This helps with plugins failing to read
  files (`django_coverage_plugin issue 78`_).

- Fix: Removed another vestige of jQuery from the source tarball
  (`issue 840`_).

- Fix: Added a default value for a new-to-6.x argument of an internal class.
  This unsupported class is being used by coveralls (`issue 1273`_). Although
  I'd rather not "fix" unsupported interfaces, it's actually nicer with a
  default value.

.. _django_coverage_plugin issue 78: https://github.com/nedbat/django_coverage_plugin/issues/78
.. _issue 1147: https://github.com/nedbat/coveragepy/issues/1147
.. _issue 1270: https://github.com/nedbat/coveragepy/issues/1270
.. _issue 1271: https://github.com/nedbat/coveragepy/issues/1271
.. _issue 1273: https://github.com/nedbat/coveragepy/issues/1273


.. _changes_611:

Version 6.1.1 — 2021-10-31
--------------------------

- Fix: The sticky header on the HTML report didn't work unless you had branch
  coverage enabled. This is now fixed: the sticky header works for everyone.
  (Do people still use coverage without branch measurement!? j/k)

- Fix: When using explicitly declared namespace packages, the "already imported
  a file that will be measured" warning would be issued (`issue 888`_).  This
  is now fixed.

.. _issue 888: https://github.com/nedbat/coveragepy/issues/888


.. _changes_61:

Version 6.1 — 2021-10-30
------------------------

- Deprecated: The ``annotate`` command and the ``Coverage.annotate`` function
  will be removed in a future version, unless people let me know that they are
  using it.  Instead, the ``html`` command gives better-looking (and more
  accurate) output, and the ``report -m`` command will tell you line numbers of
  missing lines.  Please get in touch if you have a reason to use ``annotate``
  over those better options: ned@nedbatchelder.com.

- Feature: Coverage now sets an environment variable, ``COVERAGE_RUN`` when
  running your code with the ``coverage run`` command.  The value is not
  important, and may change in the future.  Closes `issue 553`_.

- Feature: The HTML report pages for Python source files now have a sticky
  header so the file name and controls are always visible.

- Feature: The ``xml`` and ``json`` commands now describe what they wrote
  where.

- Feature: The ``html``, ``combine``, ``xml``, and ``json`` commands all accept
  a ``-q/--quiet`` option to suppress the messages they write to stdout about
  what they are doing (`issue 1254`_).

- Feature: The ``html`` command writes a ``.gitignore`` file into the HTML
  output directory, to prevent the report from being committed to git.  If you
  want to commit it, you will need to delete that file.  Closes `issue 1244`_.

- Feature: Added support for PyPy 3.8.

- Fix: More generated code is now excluded from measurement.  Code such as
  `attrs`_ boilerplate, or doctest code, was being measured though the
  synthetic line numbers meant they were never reported.  Once Cython was
  involved though, the generated .so files were parsed as Python, raising
  syntax errors, as reported in `issue 1160`_.  This is now fixed.

- Fix: When sorting human-readable names, numeric components are sorted
  correctly: file10.py will appear after file9.py.  This applies to file names,
  module names, environment variables, and test contexts.

- Performance: Branch coverage measurement is faster, though you might only
  notice on code that is executed many times, such as long-running loops.

- Build: jQuery is no longer used or vendored (`issue 840`_ and `issue 1118`_).
  Huge thanks to Nils Kattenbeck (septatrix) for the conversion to vanilla
  JavaScript in `pull request 1248`_.

.. _issue 553: https://github.com/nedbat/coveragepy/issues/553
.. _issue 840: https://github.com/nedbat/coveragepy/issues/840
.. _issue 1118: https://github.com/nedbat/coveragepy/issues/1118
.. _issue 1160: https://github.com/nedbat/coveragepy/issues/1160
.. _issue 1244: https://github.com/nedbat/coveragepy/issues/1244
.. _pull request 1248: https://github.com/nedbat/coveragepy/pull/1248
.. _issue 1254: https://github.com/nedbat/coveragepy/issues/1254
.. _attrs: https://www.attrs.org/


.. _changes_602:

Version 6.0.2 — 2021-10-11
--------------------------

- Namespace packages being measured weren't properly handled by the new code
  that ignores third-party packages. If the namespace package was installed, it
  was ignored as a third-party package.  That problem (`issue 1231`_) is now
  fixed.

- Packages named as "source packages" (with ``source``, or ``source_pkgs``, or
  pytest-cov's ``--cov``) might have been only partially measured.  Their
  top-level statements could be marked as unexecuted, because they were
  imported by coverage.py before measurement began (`issue 1232`_).  This is
  now fixed, but the package will be imported twice, once by coverage.py, then
  again by your test suite.  This could cause problems if importing the package
  has side effects.

- The :meth:`.CoverageData.contexts_by_lineno` method was documented to return
  a dict, but was returning a defaultdict.  Now it returns a plain dict.  It
  also no longer returns negative numbered keys.

.. _issue 1231: https://github.com/nedbat/coveragepy/issues/1231
.. _issue 1232: https://github.com/nedbat/coveragepy/issues/1232


.. _changes_601:

Version 6.0.1 — 2021-10-06
--------------------------

- In 6.0, the coverage.py exceptions moved from coverage.misc to
  coverage.exceptions. These exceptions are not part of the public supported
  API, CoverageException is. But a number of other third-party packages were
  importing the exceptions from coverage.misc, so they are now available from
  there again (`issue 1226`_).

- Changed an internal detail of how tomli is imported, so that tomli can use
  coverage.py for their own test suite (`issue 1228`_).

- Defend against an obscure possibility under code obfuscation, where a
  function can have an argument called "self", but no local named "self"
  (`pull request 1210`_).  Thanks, Ben Carlsson.

.. _pull request 1210: https://github.com/nedbat/coveragepy/pull/1210
.. _issue 1226: https://github.com/nedbat/coveragepy/issues/1226
.. _issue 1228: https://github.com/nedbat/coveragepy/issues/1228


.. _changes_60:

Version 6.0 — 2021-10-03
------------------------

- The ``coverage html`` command now prints a message indicating where the HTML
  report was written.  Fixes `issue 1195`_.

- The ``coverage combine`` command now prints messages indicating each data
  file being combined.  Fixes `issue 1105`_.

- The HTML report now includes a sentence about skipped files due to
  ``skip_covered`` or ``skip_empty`` settings.  Fixes `issue 1163`_.

- Unrecognized options in the configuration file are no longer errors. They are
  now warnings, to ease the use of coverage across versions.  Fixes `issue
  1035`_.

- Fix handling of exceptions through context managers in Python 3.10. A missing
  exception is no longer considered a missing branch from the with statement.
  Fixes `issue 1205`_.

- Fix another rarer instance of "Error binding parameter 0 - probably
  unsupported type." (`issue 1010`_).

- Creating a directory for the coverage data file now is safer against
  conflicts when two coverage runs happen simultaneously (`pull 1220`_).
  Thanks, Clément Pit-Claudel.

.. _issue 1035: https://github.com/nedbat/coveragepy/issues/1035
.. _issue 1105: https://github.com/nedbat/coveragepy/issues/1105
.. _issue 1163: https://github.com/nedbat/coveragepy/issues/1163
.. _issue 1195: https://github.com/nedbat/coveragepy/issues/1195
.. _issue 1205: https://github.com/nedbat/coveragepy/issues/1205
.. _pull 1220: https://github.com/nedbat/coveragepy/pull/1220


.. _changes_60b1:

Version 6.0b1 — 2021-07-18
--------------------------

- Dropped support for Python 2.7, PyPy 2, and Python 3.5.

- Added support for the Python 3.10 ``match/case`` syntax.

- Data collection is now thread-safe.  There may have been rare instances of
  exceptions raised in multi-threaded programs.

- Plugins (like the `Django coverage plugin`_) were generating "Already
  imported a file that will be measured" warnings about Django itself.  These
  have been fixed, closing `issue 1150`_.

- Warnings generated by coverage.py are now real Python warnings.

- Using ``--fail-under=100`` with coverage near 100% could result in the
  self-contradictory message :code:`total of 100 is less than fail-under=100`.
  This bug (`issue 1168`_) is now fixed.

- The ``COVERAGE_DEBUG_FILE`` environment variable now accepts ``stdout`` and
  ``stderr`` to write to those destinations.

- TOML parsing now uses the `tomli`_ library.

- Some minor changes to usually invisible details of the HTML report:

  - Use a modern hash algorithm when fingerprinting, for high-security
    environments (`issue 1189`_).  When generating the HTML report, we save the
    hash of the data, to avoid regenerating an unchanged HTML page. We used to
    use MD5 to generate the hash, and now use SHA-3-256.  This was never a
    security concern, but security scanners would notice the MD5 algorithm and
    raise a false alarm.

  - Change how report file names are generated, to avoid leading underscores
    (`issue 1167`_), to avoid rare file name collisions (`issue 584`_), and to
    avoid file names becoming too long (`issue 580`_).

.. _Django coverage plugin: https://pypi.org/project/django-coverage-plugin/
.. _issue 580: https://github.com/nedbat/coveragepy/issues/580
.. _issue 584: https://github.com/nedbat/coveragepy/issues/584
.. _issue 1150: https://github.com/nedbat/coveragepy/issues/1150
.. _issue 1167: https://github.com/nedbat/coveragepy/issues/1167
.. _issue 1168: https://github.com/nedbat/coveragepy/issues/1168
.. _issue 1189: https://github.com/nedbat/coveragepy/issues/1189
.. _tomli: https://pypi.org/project/tomli/


.. _changes_56b1:

Version 5.6b1 — 2021-04-13
--------------------------

Note: 5.6 final was never released. These changes are part of 6.0.

- Third-party packages are now ignored in coverage reporting.  This solves a
  few problems:

  - Coverage will no longer report about other people's code (`issue 876`_).
    This is true even when using ``--source=.`` with a venv in the current
    directory.

  - Coverage will no longer generate "Already imported a file that will be
    measured" warnings about coverage itself (`issue 905`_).

- The HTML report uses j/k to move up and down among the highlighted chunks of
  code.  They used to highlight the current chunk, but 5.0 broke that behavior.
  Now the highlighting is working again.

- The JSON report now includes ``percent_covered_display``, a string with the
  total percentage, rounded to the same number of decimal places as the other
  reports' totals.

.. _issue 876: https://github.com/nedbat/coveragepy/issues/876
.. _issue 905: https://github.com/nedbat/coveragepy/issues/905


.. _changes_55:

Version 5.5 — 2021-02-28
------------------------

- ``coverage combine`` has a new option, ``--keep`` to keep the original data
  files after combining them.  The default is still to delete the files after
  they have been combined.  This was requested in `issue 1108`_ and implemented
  in `pull request 1110`_.  Thanks, Éric Larivière.

- When reporting missing branches in ``coverage report``, branches aren't
  reported that jump to missing lines.  This adds to the long-standing behavior
  of not reporting branches from missing lines.  Now branches are only reported
  if both the source and destination lines are executed.  Closes both `issue
  1065`_ and `issue 955`_.

- Minor improvements to the HTML report:

  - The state of the line visibility selector buttons is saved in local storage
    so you don't have to fiddle with them so often, fixing `issue 1123`_.

  - It has a little more room for line numbers so that 4-digit numbers work
    well, fixing `issue 1124`_.

- Improved the error message when combining line and branch data, so that users
  will be more likely to understand what's happening, closing `issue 803`_.

.. _issue 803: https://github.com/nedbat/coveragepy/issues/803
.. _issue 955: https://github.com/nedbat/coveragepy/issues/955
.. _issue 1065: https://github.com/nedbat/coveragepy/issues/1065
.. _issue 1108: https://github.com/nedbat/coveragepy/issues/1108
.. _pull request 1110: https://github.com/nedbat/coveragepy/pull/1110
.. _issue 1123: https://github.com/nedbat/coveragepy/issues/1123
.. _issue 1124: https://github.com/nedbat/coveragepy/issues/1124


.. _changes_54:

Version 5.4 — 2021-01-24
------------------------

- The text report produced by ``coverage report`` now always outputs a TOTAL
  line, even if only one Python file is reported.  This makes regex parsing
  of the output easier.  Thanks, Judson Neer.  This had been requested a number
  of times (`issue 1086`_, `issue 922`_, `issue 732`_).

- The ``skip_covered`` and ``skip_empty`` settings in the configuration file
  can now be specified in the ``[html]`` section, so that text reports and HTML
  reports can use separate settings.  The HTML report will still use the
  ``[report]`` settings if there isn't a value in the ``[html]`` section.
  Closes `issue 1090`_.

- Combining files on Windows across drives now works properly, fixing `issue
  577`_.  Thanks, `Valentin Lab <pr1080_>`_.

- Fix an obscure warning from deep in the _decimal module, as reported in
  `issue 1084`_.

- Update to support Python 3.10 alphas in progress, including `PEP 626: Precise
  line numbers for debugging and other tools <pep626_>`_.

.. _issue 577: https://github.com/nedbat/coveragepy/issues/577
.. _issue 732: https://github.com/nedbat/coveragepy/issues/732
.. _issue 922: https://github.com/nedbat/coveragepy/issues/922
.. _issue 1084: https://github.com/nedbat/coveragepy/issues/1084
.. _issue 1086: https://github.com/nedbat/coveragepy/issues/1086
.. _issue 1090: https://github.com/nedbat/coveragepy/issues/1090
.. _pr1080: https://github.com/nedbat/coveragepy/pull/1080
.. _pep626: https://www.python.org/dev/peps/pep-0626/


.. _changes_531:

Version 5.3.1 — 2020-12-19
--------------------------

- When using ``--source`` on a large source tree, v5.x was slower than previous
  versions.  This performance regression is now fixed, closing `issue 1037`_.

- Mysterious SQLite errors can happen on PyPy, as reported in `issue 1010`_. An
  immediate retry seems to fix the problem, although it is an unsatisfying
  solution.

- The HTML report now saves the sort order in a more widely supported way,
  fixing `issue 986`_.  Thanks, Sebastián Ramírez (`pull request 1066`_).

- The HTML report pages now have a :ref:`Sleepy Snake <sleepy>` favicon.

- Wheels are now provided for manylinux2010, and for PyPy3 (pp36 and pp37).

- Continuous integration has moved from Travis and AppVeyor to GitHub Actions.

.. _issue 986: https://github.com/nedbat/coveragepy/issues/986
.. _issue 1037: https://github.com/nedbat/coveragepy/issues/1037
.. _issue 1010: https://github.com/nedbat/coveragepy/issues/1010
.. _pull request 1066: https://github.com/nedbat/coveragepy/pull/1066

.. _changes_53:

Version 5.3 — 2020-09-13
------------------------

- The ``source`` setting has always been interpreted as either a file path or a
  module, depending on which existed.  If both interpretations were valid, it
  was assumed to be a file path.  The new ``source_pkgs`` setting can be used
  to name a package to disambiguate this case.  Thanks, Thomas Grainger. Fixes
  `issue 268`_.

- If a plugin was disabled due to an exception, we used to still try to record
  its information, causing an exception, as reported in `issue 1011`_.  This is
  now fixed.

.. _issue 268: https://github.com/nedbat/coveragepy/issues/268
.. _issue 1011: https://github.com/nedbat/coveragepy/issues/1011


.. endchangesinclude

Older changes
-------------

The complete history is available in the `coverage.py docs`__.

__ https://coverage.readthedocs.io/en/latest/changes.html
