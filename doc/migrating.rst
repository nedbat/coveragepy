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

- The :ref:`config_report_exclude_also` setting is new in 7.2.0.  It adds
  exclusion regexes while keeping the default built-in set. It's better than
  the older :ref:`config_report_exclude_lines` setting, which overwrote the
  entire list.  Newer versions of coverage.py will be adding to the default set
  of exclusions.  Using ``exclude_also`` will let you benefit from those
  updates.
