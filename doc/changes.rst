.. _change:

:history: 20090524T134300, brand new docs.

------------------------------------
Major change history for coverage.py
------------------------------------

These are the major changes for coverage.py.  For a more complete change history,
see the `CHANGES.txt <http://bitbucket.org/ned/coveragepy/src/tip/CHANGES.txt>`_
file.

Version 3.0b3, 16 May 2009
--------------------------

- Added parameters to coverage.__init__ for options that had been set on the
  coverage object itself.
  
- Added clear_exclude() and get_exclude_list() methods for programmatic
  manipulation of the exclude regexes.

- Added coverage.load() to read previously-saved data from the data file.

- When using the object api (that is, constructing a coverage() object), data
  is no longer saved automatically on process exit.  You can re-enable it with
  the auto_data=True parameter on the coverage() constructor. The module-level
  interface still uses automatic saving.


Version 3.0b2, 30 April 2009
----------------------------

HTML reporting, and continued refactoring.

- HTML reports and annotation of source files: use the new -b (browser) switch.
  Thanks to George Song for code, inspiration and guidance.

- Code in the Python standard library is not measured by default.  If you need
  to measure standard library code, use the -L command-line switch during
  execution, or the cover_pylib=True argument to the coverage() constructor.

- coverage.annotate_file is no longer available.

- Removed the undocumented cache_file argument to coverage.usecache().


Version 3.0b1, 7 March 2009
---------------------------

Major overhaul.

- Coverage is now a package rather than a module.  Functionality has been split
  into classes.

- The trace function is implemented in C for speed.  Coverage runs are now
  much faster.  Thanks to David Christian for productive micro-sprints and
  other encouragement.

- The minimum supported Python version is 2.3.
 
