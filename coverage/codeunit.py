"""Code unit (module) handling for Coverage."""

import os

from coverage.backward import unicode_class
from coverage.files import FileLocator


class CodeUnit(object):
    """Code unit: a filename or module.

    Instance attributes:

    `name` is a human-readable name for this code unit.
    `filename` is the os path from which we can read the source.
    `relative` is a boolean.

    """

    def __init__(self, morf, file_locator=None):
        self.file_locator = file_locator or FileLocator()

        if hasattr(morf, '__file__'):
            f = morf.__file__
        else:
            f = morf
        f = self._adjust_filename(f)
        self.filename = self.file_locator.canonical_filename(f)

        if hasattr(morf, '__name__'):
            n = modname = morf.__name__
            self.relative = True
        else:
            n = os.path.splitext(morf)[0]
            rel = self.file_locator.relative_filename(n)
            if os.path.isabs(n):
                self.relative = (rel != n)
            else:
                self.relative = True
            n = rel
            modname = None
        self.name = n
        self.modname = modname

    def __repr__(self):
        return (
            "<{self.__class__.__name__}"
            " name={self.name!r}"
            " filename={self.filename!r}>".format(self=self)
        )

    def _adjust_filename(self, f):
        # TODO: This shouldn't be in the base class, right?
        return f

    # Annoying comparison operators. Py3k wants __lt__ etc, and Py2k needs all
    # of them defined.

    def __lt__(self, other):
        return self.name < other.name

    def __le__(self, other):
        return self.name <= other.name

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return self.name != other.name

    def __gt__(self, other):
        return self.name > other.name

    def __ge__(self, other):
        return self.name >= other.name

    def flat_rootname(self):
        """A base for a flat filename to correspond to this code unit.

        Useful for writing files about the code where you want all the files in
        the same directory, but need to differentiate same-named files from
        different directories.

        For example, the file a/b/c.py will return 'a_b_c'

        """
        if self.modname:
            return self.modname.replace('.', '_')
        else:
            root = os.path.splitdrive(self.name)[1]
            return root.replace('\\', '_').replace('/', '_').replace('.', '_')

    def source(self):
        """Return the source for the code, a Unicode string."""
        return unicode_class("???")

    def source_token_lines(self):
        """Return the 'tokenized' text for the code."""
        # A generic implementation, each line is one "txt" token.
        for line in self.source().splitlines():
            yield [('txt', line)]

    def should_be_python(self):
        """Does it seem like this file should contain Python?

        This is used to decide if a file reported as part of the execution of
        a program was really likely to have contained Python in the first
        place.
        """
        return False

    def get_parser(self, exclude=None):
        raise NotImplementedError
