.. _change:

====================================
Major change history for coverage.py
====================================

:history: 20090524T134300, brand new docs.
:history: 20090613T164000, final touches for 3.0
:history: 20090706T205000, changes for 3.0.1
:history: 20091004T170700, changes for 3.1
:history: 20091128T072200, changes for 3.2
:history: 20091205T161525, 3.2 final
:history: 20100221T151900, changes for 3.3

These are the major changes for coverage.py.  For a more complete change
history, see the `CHANGES.txt`_ file in the source tree.

.. _CHANGES.txt: http://bitbucket.org/ned/coveragepy/src/tip/CHANGES.txt


Version 3.3
-----------

- Settings are now read from a .coveragerc file.  A specific file can be
  specified on the command line with --rcfile=FILE.  The name of the file can
  be programmatically set with the `config_file` argument to the coverage()
  constructor, or reading a config file can be disabled with
  `config_file=False`.

- Added coverage.process_start to enable coverage measurement when Python
  starts.

- Parallel data file names now have a random number appended to them in
  addition to the machine name and process id. Also, parallel data files
  combined with "coverage combine" are deleted after they're combined, to clean
  up unneeded files. Fixes `issue 40`_.

- Exceptions thrown from product code run with "coverage run" are now displayed
  without internal coverage.py frames, so the output is the same as when the
  code is run without coverage.py.

- Fixed `issue 39`_ and `issue 47`.

.. _issue 39: http://bitbucket.org/ned/coveragepy/issue/39
.. _issue 40: http://bitbucket.org/ned/coveragepy/issue/40
.. _issue 47: http://bitbucket.org/ned/coveragepy/issue/47


Version 3.2, 5 December 2009
----------------------------

- Branch coverage: coverage.py can tell you which branches didn't have both (or
  all) choices executed, even where the choice doesn't affect which lines were
  executed.  See :ref:`Branch Coverage <branch>` for more details.

- The table of contents in the HTML report is now sortable: click the headers
  on any column.  The sorting is persisted so that subsequent reports are
  sorted as you wish.  Thanks, `Chris Adams`_.

- XML reporting has file paths that let Cobertura find the source code, fixing
  `issue 21`_.

- The ``--omit`` option now works much better than before, fixing `issue 14`_
  and `issue 33`_.  Thanks, Danek Duvall.

- Added a ``--version`` option on the command line.

- Program execution under coverage is a few percent faster.

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


Version 3.1, 4 October 2009
---------------------------

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

- Source code can now be read from eggs.  Thanks, `Ross Lawley`_.  Fixes
  `issue 25`_.

.. _Ross Lawley: http://agileweb.org/
.. _issue 25: http://bitbucket.org/ned/coveragepy/issue/25
.. _issue 12: http://bitbucket.org/ned/coveragepy/issue/12
.. _issue 13: http://bitbucket.org/ned/coveragepy/issue/13


Version 3.0.1, 7 July 2009
--------------------------

- Removed the recursion limit in the tracer function.  Previously, code that
  ran more than 500 frames deep would crash.

- Fixed a bizarre problem involving pyexpat, whereby lines following XML parser
  invocations could be overlooked.

- On Python 2.3, coverage.py could mis-measure code with exceptions being
  raised.  This is now fixed.

- The coverage.py code itself will now not be measured by coverage.py, and no
  coverage modules will be mentioned in the nose ``--with-cover`` plugin.

- When running source files, coverage.py now opens them in universal newline
  mode just like Python does.  This lets it run Windows files on Mac, for
  example.


Version 3.0, 13 June 2009
-------------------------

- Coverage is now a package rather than a module.  Functionality has been split
  into classes.

- HTML reports and annotation of source files: use the new ``-b`` (browser)
  switch.  Thanks to George Song for code, inspiration and guidance.

- The trace function is implemented in C for speed.  Coverage runs are now
  much faster.  Thanks to David Christian for productive micro-sprints and
  other encouragement.

- The minimum supported Python version is 2.3.

- When using the object api (that is, constructing a coverage() object), data
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
