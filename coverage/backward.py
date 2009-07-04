"""Add things to old Pythons so I can pretend they are newer."""

# pylint: disable-msg=W0622
# (Redefining built-in blah)
# The whole point of this file is to redefine built-ins, so shut up about it.


# Python 2.3 doesn't have `set`
try:
    set = set       # new in 2.4
except NameError:
    # (Redefining built-in 'set')
    from sets import Set as set


# Python 2.3 doesn't have `sorted`.
try:
    sorted = sorted
except NameError:
    def sorted(iterable):
        """A 2.3-compatible implementation of `sorted`."""
        lst = list(iterable)
        lst.sort()
        return lst
