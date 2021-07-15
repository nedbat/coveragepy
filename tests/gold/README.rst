.. Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
.. For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

Gold files
==========

These are files used in comparisons for some of the tests.  Code to support
these comparisons is in tests/goldtest.py.

If gold tests are failing, you may need to update the gold files by copying the
current output of the tests into the gold files. When a test fails, the actual
output is in the tests/actual directory. Do not commit those files to git.

You can run just the failed tests again with::

    tox -e py39 -- -n 0 --lf

The saved HTML files in the html directories can't be viewed properly without
the supporting CSS and Javascript files. But we don't want to save copies of
those files in every subdirectory.  There's a Makefile in the html directory
for working with the saved copies of the support files.

If the output files are correct, you can update the gold files with "make
update-gold".  If there are version-specific gold files (for example,
bom/2/\*), you'll need to update them manually.
