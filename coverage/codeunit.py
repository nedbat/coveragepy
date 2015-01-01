"""Code unit (module) handling for Coverage."""

import os
import sys

from coverage.backward import string_class, unicode_class
from coverage.files import get_python_source, FileLocator
from coverage.misc import CoverageException
from coverage.parser import PythonParser
from coverage.phystokens import source_token_lines, source_encoding


def code_units_factory(morfs, file_locator=None, get_plugin=None):
    """Construct a list of CodeUnits from modules or filenames.

    `morfs` is a module or filename, or a list of the same.

    `file_locator` is a FileLocator that can help resolve filenames.

    `get_plugin` is a function taking a filename, and returning a plugin
    responsible for the file.  It can also return None if there is no plugin
    claiming the file.

    Returns a list of CodeUnit objects.

    """
    # Be sure we have a list.
    if not isinstance(morfs, (list, tuple)):
        morfs = [morfs]

    code_units = []
    for morf in morfs:
        file_reporter = code_unit_factory(morf, file_locator, get_plugin)
        code_units.append(file_reporter)

    return code_units


def code_unit_factory(morf, file_locator=None, get_plugin=None):
    """Construct a CodeUnit from a module or filename.

    `morfs` is a module or a filename.

    `file_locator` is a FileLocator that can help resolve filenames.

    `get_plugin` is a function taking a filename, and returning a plugin
    responsible for the file.  It can also return None if there is no plugin
    claiming the file.

    Returns a CodeUnit object.

    """
    plugin = None

    if isinstance(morf, string_class) and get_plugin:
        plugin = get_plugin(morf)

    if plugin:
        file_reporter = plugin.file_reporter(morf)
        if file_reporter is None:
            raise CoverageException(
                "Plugin %r did not provide a file reporter for %r." % (
                    plugin.plugin_name, morf
                )
            )
    else:
        file_reporter = PythonCodeUnit(morf, file_locator)

    return file_reporter


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


class PythonCodeUnit(CodeUnit):
    """Represents a Python file."""

    def __init__(self, morf, file_locator=None):
        super(PythonCodeUnit, self).__init__(morf, file_locator)
        self._source = None

    def _adjust_filename(self, fname):
        # .pyc files should always refer to a .py instead.
        if fname.endswith(('.pyc', '.pyo')):
            fname = fname[:-1]
        elif fname.endswith('$py.class'):   # Jython
            fname = fname[:-9] + ".py"
        return fname

    def source(self):
        if self._source is None:
            self._source = get_python_source(self.filename)
            if sys.version_info < (3, 0):
                encoding = source_encoding(self._source)
                self._source = self._source.decode(encoding, "replace")
            assert isinstance(self._source, unicode_class)
        return self._source

    def get_parser(self, exclude=None):
        return PythonParser(filename=self.filename, exclude=exclude)

    def should_be_python(self):
        """Does it seem like this file should contain Python?

        This is used to decide if a file reported as part of the execution of
        a program was really likely to have contained Python in the first
        place.

        """
        # Get the file extension.
        _, ext = os.path.splitext(self.filename)

        # Anything named *.py* should be Python.
        if ext.startswith('.py'):
            return True
        # A file with no extension should be Python.
        if not ext:
            return True
        # Everything else is probably not Python.
        return False

    def source_token_lines(self):
        return source_token_lines(self.source())
