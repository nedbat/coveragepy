"""Add things to old Pythons so I can pretend they are newer, for tests."""

# pylint: disable=redefined-builtin
# (Redefining built-in blah)
# The whole point of this file is to redefine built-ins, so shut up about it.


# No more execfile in Py3
try:
    execfile = execfile
except NameError:
    def execfile(filename, globs):
        """A Python 3 implementation of execfile."""
        with open(filename) as fobj:
            code = fobj.read()
        exec(compile(code, filename, 'exec'), globs)
