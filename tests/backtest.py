# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Add things to old Pythons so I can pretend they are newer, for tests."""

# No more execfile in Py3
try:
    execfile = execfile
except NameError:
    def execfile(filename, globs):
        """A Python 3 implementation of execfile."""
        with open(filename) as fobj:
            code = fobj.read()
        exec(compile(code, filename, 'exec'), globs)
