"""Plugin interfaces for coverage.py"""

import os
import re

from coverage.misc import _needs_to_implement


class CoveragePlugin(object):
    """Base class for coverage.py plugins.

    To write a coverage.py plugin, create a subclass of `CoveragePlugin`.
    You can override methods here to participate in various aspects of
    coverage.py's processing.

    Currently the only plugin type is a file tracer, for implementing
    measurement support for non-Python files.  File tracer plugins implement
    the :meth:`file_tracer` method to claim files and the :meth:`file_reporter`
    method to report on those files.

    Any plugin can optionally implement :meth:`sys_info` to provide debugging
    information about their operation.

    """

    def __init__(self, options):
        """
        When the plugin is constructed, it will be passed a dictionary of
        plugin-specific options read from the .coveragerc configuration file.
        The base class stores these on the `self.options` attribute.

        Arguments:
            options (dict): The plugin-specific options read from the
                .coveragerc configuration file.

        """
        self.options = options

    def file_tracer(self, filename):        # pylint: disable=unused-argument
        """Return a FileTracer object for a file.

        Every source file is offered to the plugin to give it a chance to take
        responsibility for tracing the file.  If your plugin can handle the
        file, then return a :class:`FileTracer` object.  Otherwise return None.

        There is no way to register your plugin for particular files.  Instead,
        this method is invoked for all files, and can decide whether it can
        trace the file or not.  Be prepared for `filename` to refer to all kinds
        of files that have nothing to do with your plugin.

        Arguments:
            filename (str): The path to the file being considered.  This is the
                absolute real path to the file.  If you are comparing to other
                paths, be sure to take this into account.

        Returns:
            FileTracer: the :class:`FileTracer` object to use to trace
                `filename`, or None if this plugin cannot trace this file.

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

        Returns:
            The filename to credit with this execution.

        """
        _needs_to_implement(self, "source_filename")

    def has_dynamic_source_filename(self):
        """Does this FileTracer have dynamic source filenames?

        FileTracers can provide dynamically determined filenames by
        implementing dynamic_source_filename.  Invoking that function is
        expensive. To determine whether to invoke it, coverage.py uses
        the result of this function to know if it needs to bother invoking
        :meth:`dynamic_source_filename`.

        Returns:
            boolean: True if :meth:`dynamic_source_filename` should be called
                to get dynamic source filenames.

        """
        return False

    def dynamic_source_filename(self, filename, frame):     # pylint: disable=unused-argument
        """Returns a dynamically computed source filename.

        Some plugins need to compute the source filename dynamically for each
        frame.

        This function will not be invoked if
        :meth:`has_dynamic_source_filename` returns False.

        Returns:
            The source filename for this frame, or None if this frame shouldn't
                be measured.

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

        Arguments:
            frame: the call frame to examine.

        Returns:
            int, int: a pair of line numbers, the start and end lines
                executed in the source, inclusive.

        """
        lineno = frame.f_lineno
        return lineno, lineno


class FileReporter(object):
    """Support needed for files during the reporting phase."""
    def __init__(self, filename):
        # TODO: document that this init happens.
        self.filename = filename

    def __repr__(self):
        return (
            # pylint: disable=redundant-keyword-arg
            "<{self.__class__.__name__}"
            " filename={self.filename!r}>".format(self=self)
        )

    # Annoying comparison operators. Py3k wants __lt__ etc, and Py2k needs all
    # of them defined.

    def __lt__(self, other):
        return self.filename < other.filename

    def __le__(self, other):
        return self.filename <= other.filename

    def __eq__(self, other):
        return self.filename == other.filename

    def __ne__(self, other):
        return self.filename != other.filename

    def __gt__(self, other):
        return self.filename > other.filename

    def __ge__(self, other):
        return self.filename >= other.filename

    def statements(self):
        _needs_to_implement(self, "statements")

    def excluded_statements(self):
        return set([])

    def translate_lines(self, lines):
        return set(lines)

    def translate_arcs(self, arcs):
        return arcs

    def no_branch_lines(self):
        return set()

    def exit_counts(self):
        return {}

    def arcs(self):
        return []

    def source(self):
        """Return the source for the code, a Unicode string."""
        # A generic implementation: read the text of self.filename
        with open(self.filename) as f:
            return f.read()

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

    def flat_rootname(self):
        """A base for a flat filename to correspond to this file.

        Useful for writing files about the code where you want all the files in
        the same directory, but need to differentiate same-named files from
        different directories.

        For example, the file a/b/c.py will return 'a_b_c_py'

        """
        name = os.path.splitdrive(self.name)[1]
        return re.sub(r"[\\/.:]", "_", name)
