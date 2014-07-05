"""Code unit (module) handling for Coverage."""

import os

from coverage.backward import open_python_source, string_class
from coverage.misc import CoverageException, NoSource
from coverage.parser import CodeParser, PythonParser
from coverage.phystokens import source_token_lines, source_encoding

from coverage.django import DjangoTracer


def code_unit_factory(morfs, file_locator, get_ext=None):
    """Construct a list of CodeUnits from polymorphic inputs.

    `morfs` is a module or a filename, or a list of same.

    `file_locator` is a FileLocator that can help resolve filenames.

    `get_ext` TODO

    Returns a list of CodeUnit objects.

    """
    # Be sure we have a list.
    if not isinstance(morfs, (list, tuple)):
        morfs = [morfs]

    django_tracer = DjangoTracer()

    code_units = []
    for morf in morfs:
        ext = None
        if isinstance(morf, string_class) and get_ext:
            ext = get_ext(morf)
        if ext:
            klass = DjangoTracer # NOT REALLY! TODO
            # Hacked-in Mako support. Define COVERAGE_MAKO_PATH as a fragment of
            # the path that indicates the Python file is actually a compiled Mako
            # template. THIS IS TEMPORARY!
            #MAKO_PATH = os.environ.get('COVERAGE_MAKO_PATH')
            #if MAKO_PATH and isinstance(morf, string_class) and MAKO_PATH in morf:
            #    # Super hack! Do mako both ways!
            #    if 0:
            #        cu = PythonCodeUnit(morf, file_locator)
            #        cu.name += '_fako'
            #        code_units.append(cu)
            #    klass = MakoCodeUnit
            #elif isinstance(morf, string_class) and morf.endswith(".html"):
            #    klass = DjangoCodeUnit
        else:
            klass = PythonCodeUnit
        code_units.append(klass(morf, file_locator))

    return code_units


class CodeUnit(object):
    """Code unit: a filename or module.

    Instance attributes:

    `name` is a human-readable name for this code unit.
    `filename` is the os path from which we can read the source.
    `relative` is a boolean.

    """

    def __init__(self, morf, file_locator):
        self.file_locator = file_locator

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
        return "<CodeUnit name=%r filename=%r>" % (self.name, self.filename)

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
        """Return the source code, as a string."""
        if os.path.exists(self.filename):
            # A regular text file: open it.
            with open_python_source(self.filename) as f:
                return f.read()

        # Maybe it's in a zip file?
        source = self.file_locator.get_zip_data(self.filename)
        if source is not None:
            return source

        # Couldn't find source.
        raise CoverageException(
            "No source for code '%s'." % self.filename
            )

    def source_token_lines(self, source):
        """Return the 'tokenized' text for the code."""
        # TODO: Taking source here is wrong, change it?
        for line in source.splitlines():
            yield [('txt', line)]

    def should_be_python(self):
        """Does it seem like this file should contain Python?

        This is used to decide if a file reported as part of the execution of
        a program was really likely to have contained Python in the first
        place.
        """
        return False


class PythonCodeUnit(CodeUnit):
    """Represents a Python file."""

    def _adjust_filename(self, fname):
        # .pyc files should always refer to a .py instead.
        if fname.endswith(('.pyc', '.pyo')):
            fname = fname[:-1]
        elif fname.endswith('$py.class'): # Jython
            fname = fname[:-9] + ".py"
        return fname

    def get_parser(self, exclude=None):
        actual_filename, source = self._find_source(self.filename)
        return PythonParser(
            text=source, filename=actual_filename, exclude=exclude,
        )

    def _find_source(self, filename):
        """Find the source for `filename`.

        Returns two values: the actual filename, and the source.

        The source returned depends on which of these cases holds:

            * The filename seems to be a non-source file: returns None

            * The filename is a source file, and actually exists: returns None.

            * The filename is a source file, and is in a zip file or egg:
              returns the source.

            * The filename is a source file, but couldn't be found: raises
              `NoSource`.

        """
        source = None

        base, ext = os.path.splitext(filename)
        TRY_EXTS = {
            '.py':  ['.py', '.pyw'],
            '.pyw': ['.pyw'],
        }
        try_exts = TRY_EXTS.get(ext)
        if not try_exts:
            return filename, None

        for try_ext in try_exts:
            try_filename = base + try_ext
            if os.path.exists(try_filename):
                return try_filename, None
            source = self.file_locator.get_zip_data(try_filename)
            if source:
                return try_filename, source
        raise NoSource("No source for code: '%s'" % filename)

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

    def source_token_lines(self, source):
        return source_token_lines(source)

    def source_encoding(self, source):
        return source_encoding(source)


class MakoParser(CodeParser):
    def __init__(self, metadata):
        self.metadata = metadata

    def parse_source(self):
        """Returns executable_line_numbers, excluded_line_numbers"""
        executable = set(self.metadata['line_map'].values())
        return executable, set()

    def translate_lines(self, lines):
        tlines = set()
        for l in lines:
            try:
                tlines.add(self.metadata['full_line_map'][l])
            except IndexError:
                pass
        return tlines


class MakoCodeUnit(CodeUnit):
    def __init__(self, *args, **kwargs):
        super(MakoCodeUnit, self).__init__(*args, **kwargs)
        from mako.template import ModuleInfo
        py_source = open(self.filename).read()
        self.metadata = ModuleInfo.get_module_source_metadata(py_source, full_line_map=True)

    def source(self):
        return open(self.metadata['filename']).read()

    def get_parser(self, exclude=None):
        return MakoParser(self.metadata)

    def source_encoding(self, source):
        # TODO: Taking source here is wrong, change it!
        return self.metadata['source_encoding']


class DjangoCodeUnit(CodeUnit):
    def source(self):
        with open(self.filename) as f:
            return f.read()

    def get_parser(self, exclude=None):
        return DjangoParser(self.filename)

    def source_encoding(self, source):
        return "utf8"


class DjangoParser(CodeParser):
    def __init__(self, filename):
        self.filename = filename

    def parse_source(self):
        with open(self.filename) as f:
            source = f.read()
        executable = set(range(1, len(source.splitlines())+1))
        return executable, set()
