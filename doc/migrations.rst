.. Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
.. For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

.. Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
.. For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

.. _migrations:

==============================
Migrating between versions
==============================

.. _migrating_6x_7x:

Migrating 6.x.x — 7.x.x
--------------------------
- The way that wildcards when specifing file paths work in certain caseshas changed in 7.x:

  - Previously, ``*`` would incorrectly match directory separators, making
    precise matching difficult. This requires ``[paths]`` such as ``*tests/*``
    to be changed to ``*/tests/*``.
  
  - A file path setting like ``*/foo`` will now match ``foo/bar.py`` so that
    relative file paths can be combined more easily.

- When remapping file paths with ``[paths]``, a path will be remapped only if
  the resulting path exists. Ensure that remapped ``[paths]`` exist when upgrading
  as this is now being enforced.

