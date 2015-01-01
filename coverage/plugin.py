"""Plugin management for coverage.py"""


class CoveragePlugin(object):
    """Base class for coverage.py plugins."""
    def __init__(self, options):
        self.options = options

    def file_tracer(self, filename):
        """Return a FileTracer object for this file.

        Every source file is offered to the plugin to give it a chance to take
        responsibility for tracing the file.  If your plugin can handle the
        file, then return a `FileTracer` object.  Otherwise return None.

        There is no way to register your plugin for particular files.  This
        method is how your plugin applies itself to files.  Be prepared for
        `filename` to refer to all kinds of files that have nothing to do with
        your plugin.

        Arguments:
            filename (str): The path to the file being considered.  This is the
                absolute real path to the file.  If you are comparing to other
                paths, be sure to take this into account.

        Returns:
            FileTracer: the `FileTracer` object to use to trace this file, or
                None if this plugin cannot trace this file.

        """
        return None

    def file_reporter(self, filename):
        """Return the FileReporter class to use for filename.

        This will only be invoked if `filename` returns non-None from
        `file_tracer`.  It's an error to return None.

        """
        raise NotImplementedError(
            "Plugin %r needs to implement file_reporter" % self.plugin_name
            )


class FileTracer(object):
    """Support needed for files during the tracing phase.

    You may construct this object from CoveragePlugin.file_tracer any way you
    like.  A natural choice would be to pass the filename given to file_tracer.

    """

    def source_filename(self):
        """The source filename for this file.

        This may be any filename you like.  A key responsibility of a plugin is
        to own the mapping from Python execution back to whatever source
        filename was originally the source of the code.

        Returns:
            The filename to credit with this execution.

        """
        return None

    def has_dynamic_source_filename(self):
        """Does this FileTracer have dynamic source filenames?

        FileTracers can provide dynamically determined filenames by
        implementing dynamic_source_filename.  Invoking that function is
        expensive. To determine whether it should invoke it, coverage.py uses
        the result of this function to know if it needs to bother invoking
        dynamic_source_filename.

        Returns:
            A boolean, true if `dynamic_source_filename` should be called to
            get dynamic source filenames.

        """
        return False

    def dynamic_source_filename(self, filename, frame):
        """Returns a dynamically computed source filename.

        Some plugins need to compute the source filename dynamically for each
        frame.

        This function will not be invoked if `has_dynamic_source_filename`
        returns False.

        Returns:
            The source filename for this frame, or None if this frame shouldn't
            be measured.

        Can return None if dynamic filenames aren't needed.

        """
        return None

    def line_number_range(self, frame):
        """Given a call frame, return the range of source line numbers.

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
            (int, int): a pair of line numbers, the start and end lines
                executed in the source, inclusive.

        """
        lineno = frame.f_lineno
        return lineno, lineno


class FileReporter(object):
    """Support needed for files during the reporting phase."""
    def __init__(self, filename):
        self.filename = filename
