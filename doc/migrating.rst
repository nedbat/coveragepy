.. Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
.. For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

.. _migrating:

==========================
Migrating between versions
==========================

New major versions of coverage.py might require you to adjust your settings,
options, or other aspects of your use.  This page details those changes.

.. _migrating_6x_7x:

Migrating from 6.x to 7.x
-------------------------

- The way that wildcards when specifying file paths work in certain cases has changed in 7.x:

  - Previously, ``*`` would incorrectly match directory separators, making
    precise matching difficult. Patterns such as ``*tests/*``
    will need to be changed to ``*/tests/*``.

  - ``**`` now matches any number of nested directories. If you wish to retain the behavior of
    ``**/tests/*`` in previous versions then  ``*/**/tests/*`` can be used instead.

- When remapping file paths with ``[paths]``, a path will be remapped only if
  the resulting path exists. Ensure that remapped ``[paths]`` exist when upgrading
  as this is now being enforced.
