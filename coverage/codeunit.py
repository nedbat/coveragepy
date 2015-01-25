"""Code unit (module) handling for Coverage."""

import os

from coverage.files import FileLocator
from coverage.plugin import FileReporter


class CodeUnit(FileReporter):
    """Code unit: a filename or module.

    Instance attributes:

    `name` is a human-readable name for this code unit.
    `filename` is the os path from which we can read the source.

    """

    def __init__(self, morf, file_locator=None):
        self.file_locator = file_locator or FileLocator()

        if hasattr(morf, '__file__'):
            filename = morf.__file__
        else:
            filename = morf
        filename = self._adjust_filename(filename)
        self.filename = self.file_locator.canonical_filename(filename)

        if hasattr(morf, '__name__'):
            name = morf.__name__
            name = name.replace(".", os.sep) + ".py"
        else:
            name = self.file_locator.relative_filename(filename)
        self.name = name

    def _adjust_filename(self, f):
        # TODO: This shouldn't be in the base class, right?
        return f
