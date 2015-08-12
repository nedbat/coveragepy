# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

"""Plugin interfaces for coverage.py"""

from coverage import files
from coverage.misc import contract, _needs_to_implement


class CoveragePlugin(object):
    """Base class for coverage.py plugins.

    To write a coverage.py plugin, create a module with a subclass of
    :class:`CoveragePlugin`.  You can override methods in your class to
    participate in various aspects of coverage.py's processing.

    Currently the only plugin type is a file tracer, for implementing
    measurement support for non-Python files.  File tracer plugins implement
    the :meth:`file_tracer` method to claim files and the :meth:`file_reporter`
    method to report on those files.

    Any plugin can optionally implement :meth:`sys_info` to provide debugging
    information about their operation.

    Coverage.py will store its own information on your plugin, with attributes
    starting with "_coverage_".  Don't be startled.

    To register your plugin, define a function called `coverage_init` in your
    module::

        def coverage_init(reg, options):
            reg.add_file_tracer(MyPlugin())

    The `reg.add_file_tracer` method takes an instance of your plugin.  If your
    plugin takes options, the `options` argument is a dictionary of your
    plugin's options from the .coveragerc file.

    """

    def file_tracer(self, filename):        # pylint: disable=unused-argument
        """Return a FileTracer object for a file.

        Every source file is offered to the plugin to give it a chance to take
        responsibility for tracing the file.  If your plugin can handle the
        file, then return a :class:`FileTracer` object.  Otherwise return None.

        There is no way to register your plugin for particular files.  Instead,
        this method is invoked for all files, and can decide whether it can
        trace the file or not.  Be prepared for `filename` to refer to all
        kinds of files that have nothing to do with your plugin.

        `filename` is a string, the path to the file being considered.  This is
        the absolute real path to the file.  If you are comparing to other
        paths, be sure to take this into account.

        Returns a :class:`FileTracer` object to use to trace `filename`, or
        None if this plugin cannot trace this file.

        """
        return None

    def file_reporter(self, filename):      # pylint: disable=unused-argument
        """Return the FileReporter class to use for filename.

        This will only be invoked if `filename` returns non-None from
        :meth:`file_tracer`.  It's an error to return None.

        """
        _needs_to_implement(self, "file_reporter")

    def sys_info(self):
        """Return a list of information useful for debugging.

        This method will be invoked for ``--debug=sys``.  Your
        plugin can return any information it wants to be displayed.

        The return value is a list of pairs: (name, value).

        """
        return []


class FileTracer(object):
    """Support needed for files during the tracing phase.

    You may construct this object from :meth:`CoveragePlugin.file_tracer` any
    way you like.  A natural choice would be to pass the filename given to
    `file_tracer`.

    """

    def source_filename(self):
        """The source filename for this file.

        This may be any filename you like.  A key responsibility of a plugin is
        to own the mapping from Python execution back to whatever source
        filename was originally the source of the code.

        Returns the filename to credit with this execution.

        """
        _needs_to_implement(self, "source_filename")

    def has_dynamic_source_filename(self):
        """Does this FileTracer have dynamic source filenames?

        FileTracers can provide dynamically determined filenames by
        implementing dynamic_source_filename.  Invoking that function is
        expensive. To determine whether to invoke it, coverage.py uses the
        result of this function to know if it needs to bother invoking
        :meth:`dynamic_source_filename`.

        Returns true if :meth:`dynamic_source_filename` should be called to get
        dynamic source filenames.

        """
        return False

    def dynamic_source_filename(self, filename, frame):     # pylint: disable=unused-argument
        """Returns a dynamically computed source filename.

        Some plugins need to compute the source filename dynamically for each
        frame.

        This function will not be invoked if
        :meth:`has_dynamic_source_filename` returns False.

        Returns the source filename for this frame, or None if this frame
        shouldn't be measured.

        """
        return None

    def line_number_range(self, frame):
        """Return the range of source line numbers for a given a call frame.

        The call frame is examined, and the source line number in the original
        file is returned.  The return value is a pair of numbers, the starting
        line number and the ending line number, both inclusive.  For example,
        returning (5, 7) means that lines 5, 6, and 7 should be considered
        executed.

        This function might decide that the frame doesn't indicate any lines
        from the source file were executed.  Return (-1, -1) in this case to
        tell coverage.py that no lines should be recorded for this frame.

        """
        lineno = frame.f_lineno
        return lineno, lineno


class FileReporter(object):
    """Support needed for files during the reporting phase."""

    def __init__(self, filename):
        """Simple initialization of a `FileReporter`.

        The `filename` argument is the path to the file being reported.  This
        will be available as the `.filename` attribute on the object.  Other
        method implementations on this base class rely on this attribute.

        """
        self.filename = filename

    def __repr__(self):
        return "<{0.__class__.__name__} filename={0.filename!r}>".format(self)

    def relative_filename(self):
        """Return the relative filename for this file.

        This file path will be displayed in reports. You only need to supply
        this method if you have an unusual syntax for file paths.  The default
        implementation will supply the actual project-relative file path.

        """
        return files.relative_filename(self.filename)

    def lines(self):
        """Return a set of executable lines"""
        _needs_to_implement(self, "lines")

    def excluded_lines(self):
        return set()

    def arcs(self):
        return []

    def no_branch_lines(self):
        return set()

    def translate_lines(self, lines):
        return set(lines)

    def translate_arcs(self, arcs):
        return arcs

    def exit_counts(self):
        return {}

    @contract(returns='unicode')
    def source(self):
        """Return the source for the code, a Unicode string."""
        # A generic implementation: read the text of self.filename
        with open(self.filename, "rb") as f:
            return f.read().decode("utf8")

    def source_token_lines(self):
        """Generate a series of tokenized lines, one for each line in `source`.

        These tokens are used for syntax-colored reports.

        Each line is a list of pairs, each pair is a token::

            [('key', 'def'), ('ws', ' '), ('nam', 'hello'), ('op', '('), ... ]

        Each pair has a token class, and the token text.  The token classes are:

        * `'com'`: a comment
        * `'key'`: a keyword
        * `'nam'`: a name, or identifier
        * `'num'`: a number
        * `'op'`: an operator
        * `'str'`: a string literal
        * `'txt'`: some other kind of text

        If you concatenate all the token texts, and then join them with newlines,
        you should have your original `source` back.

        """
        # A generic implementation, each line is one "txt" token.
        for line in self.source().splitlines():
            yield [('txt', line)]

    # Annoying comparison operators. Py3k wants __lt__ etc, and Py2k needs all
    # of them defined.

    def __eq__(self, other):
        return isinstance(other, FileReporter) and self.filename == other.filename

    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        return self.filename < other.filename

    def __le__(self, other):
        return self.filename <= other.filename

    def __gt__(self, other):
        return self.filename > other.filename

    def __ge__(self, other):
        return self.filename >= other.filename
