"""Coverage data for Coverage."""

import glob
import os
import random
import socket

from coverage.backward import iitems, pickle
from coverage.debug import _TEST_NAME_FILE
from coverage.files import PathAliases
from coverage.misc import CoverageException, file_be_gone


class CoverageData(object):
    """Manages collected coverage data, including file storage.

    This class is the public supported API to coverage.py's data.

    .. note::

        The file format is not documented or guaranteed.  It will change in
        the future, in possibly complicated ways.  Use this API to avoid
        disruption.

    There are three kinds of data that can be collected:

    * **lines**: the line numbers of source lines that were executed.
      These are always available.

    * **arcs**: pairs of source and destination line numbers for transitions
      between source lines.  These are only available if branch coverage was
      used.

    * **plugin names**: the module names of the plugin that handled each file
      in the data.


    To read a coverage.py data file, use :meth:`read_file`, or :meth:`read` if
    you have an already-opened file.  You can then access the line, arc, or
    plugin data with :meth:`lines`, :meth:`arcs`, or :meth:`plugin_name`.

    The :meth:`has_arcs` method indicates whether arc data is available.  You
    can get a list of the files in the data with :meth:`measured_files`.
    A summary of the line data is available from :meth:`line_counts`.  As with
    most Python containers, you can determine if there is any data at all by
    using this object as a boolean value.


    Most data files will be created by coverage.py itself, but you can use
    methods here to create data files if you like.  The :meth:`add_lines`,
    :meth:`add_arcs`, and :meth:`add_plugins` methods add data, in ways that
    are convenient for coverage.py.  To add a file without any measured data,
    use :meth:`touch_file`.

    You write to a named file with :meth:`write_file`, or to an already opened
    file with :meth:`write`.

    You can clear the data in memory with :meth:`erase`.  Two data collections
    can be combined by using :meth:`update` on one `CoverageData`, passing it
    the other.

    """

    # The data file format is a pickled dict, with these keys:
    #
    #     * collector: a string identifying the collecting software
    #
    #     * lines: a dict mapping filenames to lists of line numbers
    #       executed::
    #
    #         { 'file1': [17,23,45], 'file2': [1,2,3], ... }
    #
    #     * arcs: a dict mapping filenames to lists of line number pairs::
    #
    #         { 'file1': [(17,23), (17,25), (25,26)], ... }
    #
    #     * plugins: a dict mapping filenames to plugin names::
    #
    #         { 'file1': "django.coverage", ... }
    #
    # Only one of `lines` or `arcs` will be present: with branch coverage, data
    # is stored as arcs. Without branch coverage, it is stored as lines.  The
    # line data is easily recovered from the arcs: it is all the first elements
    # of the pairs that are greater than zero.

    def __init__(self, collector=None, debug=None):
        """Create a CoverageData.

        `collector` is a string describing the coverage measurement software,
        for example, `"coverage.py v3.14"`.

        `debug` is a `DebugControl` object for writing debug messages.

        """
        self._collector = collector
        self._debug = debug

        # A map from canonical Python source file name to a dictionary in
        # which there's an entry for each line number that has been
        # executed:
        #
        #   {
        #       'filename1.py': { 12: None, 47: None, ... },
        #       ...
        #       }
        #
        self._lines = {}

        # A map from canonical Python source file name to a dictionary with an
        # entry for each pair of line numbers forming an arc:
        #
        #   {
        #       'filename1.py': { (12,14): None, (47,48): None, ... },
        #       ...
        #       }
        #
        self._arcs = {}

        # A map from canonical source file name to a plugin module name:
        #
        #   {
        #       'filename1.py': 'django.coverage',
        #       ...
        #       }
        #
        self._plugins = {}

    ##
    ## Reading data
    ##

    def has_arcs(self):
        """Does this data have arcs?

        Arc data is only available if branch coverage was used during
        collection.

        Returns a boolean.

        """
        return self._has_arcs()

    def lines(self, filename):
        """Get the list of lines executed for a file.

        If the file was not measured, returns None.  A file might be measured,
        and have no lines executed, in which case an empty list is returned.

        """
        if self._arcs:
            if filename in self._arcs:
                return [s for s, __ in self._arcs[filename] if s > 0]
        else:
            if filename in self._lines:
                return list(self._lines[filename])
        return None

    def arcs(self, filename):
        """Get the list of arcs executed for a file.

        If the file was not measured, returns None.  A file might be measured,
        and have no arcs executed, in which case an empty list is returned.

        """
        if filename in self._arcs:
            return list((self._arcs[filename]).keys())
        return None

    def plugin_name(self, filename):
        """Get the plugin name for a file.

        Arguments:
            filename: the name of the file you're interested in.

        Returns:
            str: the name of the plugin that handles this file.  If the file
                was measured, but didn't use a plugin, then "" is returned.
                If the file was not measured, then None is returned.

        """
        # Because the vast majority of files involve no plugin, we don't store
        # them explicitly in self._plugins.  Check the measured data instead
        # to see if it was a known file with no plugin.
        if filename in (self._arcs or self._lines):
            return self._plugins.get(filename, "")
        return None

    def measured_files(self):
        """A list of all files that had been measured."""
        return list(self._arcs or self._lines)

    def line_counts(self, fullpath=False):
        """Return a dict summarizing the line coverage data.

        Keys are based on the filenames, and values are the number of executed
        lines.  If `fullpath` is true, then the keys are the full pathnames of
        the files, otherwise they are the basenames of the files.

        Returns:
            dict mapping filenames to counts of lines.

        """
        summ = {}
        if fullpath:
            filename_fn = lambda f: f
        else:
            filename_fn = os.path.basename
        for filename in self.measured_files():
            summ[filename_fn(filename)] = len(self.lines(filename))
        return summ

    def __nonzero__(self):
        return bool(self._lines) or bool(self._arcs)

    __bool__ = __nonzero__

    def read(self, file_obj):
        """Read the coverage data from the given file object.

        Should only be used on an empty CoverageData object.

        """
        data = pickle.load(file_obj)

        # Unpack the 'lines' item.
        self._lines = dict([
            (f, dict.fromkeys(linenos, None))
            for f, linenos in iitems(data.get('lines', {}))
        ])
        # Unpack the 'arcs' item.
        self._arcs = dict([
            (f, dict.fromkeys(arcpairs, None))
            for f, arcpairs in iitems(data.get('arcs', {}))
        ])
        self._plugins = data.get('plugins', {})

    def read_file(self, filename):
        """Read the coverage data from `filename` into this object."""
        if self._debug and self._debug.should('dataio'):
            self._debug.write("Reading data from %r" % (filename,))
        try:
            with open(filename, "rb") as f:
                self.read(f)
        except Exception as exc:
            raise CoverageException(
                "Couldn't read data from '%s': %s: %s" % (
                    filename, exc.__class__.__name__, exc,
                )
            )

    ##
    ## Writing data
    ##

    def add_lines(self, line_data):
        """Add executed line data.

        `line_data` is { filename: { lineno: None, ... }, ...}

        """
        if self._has_arcs():
            raise CoverageException("Can't add lines to existing arc data")

        for filename, linenos in iitems(line_data):
            self._lines.setdefault(filename, {}).update(linenos)

    def add_arcs(self, arc_data):
        """Add measured arc data.

        `arc_data` is { filename: { (l1,l2): None, ... }, ...}

        """
        if self._has_lines():
            raise CoverageException("Can't add arcs to existing line data")

        for filename, arcs in iitems(arc_data):
            self._arcs.setdefault(filename, {}).update(arcs)

    def add_plugins(self, plugin_data):
        """Add per-file plugin information.

        `plugin_data` is { filename: plugin_name, ... }

        """
        existing_files = self._arcs or self._lines
        for filename, plugin_name in iitems(plugin_data):
            if filename not in existing_files:
                raise CoverageException(
                    "Can't add plugin data for unmeasured file '%s'" % (filename,)
                )
            existing_plugin = self._plugins.get(filename)
            if existing_plugin is not None and plugin_name != existing_plugin:
                raise CoverageException(
                    "Conflicting plugin name for '%s': %r vs %r" % (
                        filename, existing_plugin, plugin_name,
                    )
                )
            self._plugins[filename] = plugin_name

    def touch_file(self, filename):
        """Ensure that `filename` appears in the data, empty if needed."""
        (self._arcs or self._lines).setdefault(filename, {})

    def write(self, file_obj):
        """Write the coverage data to `file_obj`."""

        # Create the file data.
        file_data = {}

        if self._arcs:
            file_data['arcs'] = dict((f, list(amap.keys())) for f, amap in iitems(self._arcs))
        else:
            file_data['lines'] = dict((f, list(lmap.keys())) for f, lmap in iitems(self._lines))

        if self._collector:
            file_data['collector'] = self._collector

        file_data['plugins'] = self._plugins

        # Write the pickle to the file.
        pickle.dump(file_data, file_obj, 2)

    def write_file(self, filename):
        """Write the coverage data to `filename`."""
        if self._debug and self._debug.should('dataio'):
            self._debug.write("Writing data to %r" % (filename,))
        with open(filename, 'wb') as fdata:
            self.write(fdata)

    def erase(self):
        """Erase the data in this object."""
        self._lines = {}
        self._arcs = {}
        self._plugins = {}

    def update(self, other_data, aliases=None):
        """Update this data with data from another `CoverageData`.

        If `aliases` is provided, it's a `PathAliases` object that is used to
        re-map paths to match the local machine's.

        """
        if self._has_lines() and other_data._has_arcs():
            raise CoverageException("Can't combine arc data with line data")
        if self._has_arcs() and other_data._has_lines():
            raise CoverageException("Can't combine line data with arc data")

        aliases = aliases or PathAliases()

        # _plugins: only have a string, so they have to agree.
        # Have to do these first, so that our examination of self._arcs and
        # self._lines won't be confused by data updated from other_data.
        for filename in other_data.measured_files():
            other_plugin = other_data.plugin_name(filename)
            filename = aliases.map(filename)
            this_plugin = self.plugin_name(filename)
            if this_plugin is None:
                self._plugins[filename] = other_plugin
            elif this_plugin != other_plugin:
                raise CoverageException(
                    "Conflicting plugin name for '%s': %r vs %r" % (
                        filename, this_plugin, other_plugin,
                    )
                )

        # _lines: merge dicts.
        for filename, file_data in iitems(other_data._lines):
            filename = aliases.map(filename)
            self._lines.setdefault(filename, {}).update(file_data)

        # _arcs: merge dicts.
        for filename, file_data in iitems(other_data._arcs):
            filename = aliases.map(filename)
            self._arcs.setdefault(filename, {}).update(file_data)

    ##
    ## Miscellaneous
    ##

    def add_to_hash(self, filename, hasher):
        """Contribute `filename`'s data to the `hasher`.

        Arguments:
            filename (str): the filename we're interested in.
            hasher (:class:`coverage.misc.Hasher`): the Hasher to update with
                the file's data.

        """
        if self._arcs:
            hasher.update(sorted(self.arcs(filename)))
        else:
            hasher.update(sorted(self.lines(filename)))
        hasher.update(self.plugin_name(filename))

    ##
    ## Internal
    ##

    def _has_lines(self):
        """Do we have data in self._lines?"""
        return bool(self._lines)

    def _has_arcs(self):
        """Do we have data in self._arcs?"""
        return bool(self._arcs)


class CoverageDataFiles(object):
    """Manage the use of coverage data files."""

    def __init__(self, basename=None):
        """Create a CoverageDataFiles to manage data files.

        `basename` is the name of the file to use for storing data.

        """
        # Construct the filename that will be used for data storage.
        self.filename = os.path.abspath(basename or ".coverage")

    def erase(self):
        """Erase the data from the file storage."""
        file_be_gone(self.filename)

    def read(self, data):
        """Read the coverage data."""
        if os.path.exists(self.filename):
            data.read_file(self.filename)

    def write(self, data, suffix=None):
        """Write the collected coverage data to a file.

        `suffix` is a suffix to append to the base file name. This can be used
        for multiple or parallel execution, so that many coverage data files
        can exist simultaneously.  A dot will be used to join the base name and
        the suffix.

        """
        filename = self.filename
        if suffix is True:
            # If data_suffix was a simple true value, then make a suffix with
            # plenty of distinguishing information.  We do this here in
            # `save()` at the last minute so that the pid will be correct even
            # if the process forks.
            extra = ""
            if _TEST_NAME_FILE:                             # pragma: debugging
                with open(_TEST_NAME_FILE) as f:
                    test_name = f.read()
                extra = "." + test_name
            suffix = "%s%s.%s.%06d" % (
                socket.gethostname(), extra, os.getpid(),
                random.randint(0, 999999)
            )

        if suffix:
            filename += "." + suffix
        data.write_file(filename)

    def combine_parallel_data(self, data, aliases=None, data_dirs=None):
        """Combine a number of data files together.

        Treat `self.filename` as a file prefix, and combine the data from all
        of the data files starting with that prefix plus a dot.

        If `aliases` is provided, it's a `PathAliases` object that is used to
        re-map paths to match the local machine's.

        If `data_dirs` is provided, then it combines the data files from each
        directory into a single file.

        """
        data_dir, local = os.path.split(self.filename)
        localdot = local + '.*'

        data_dirs = data_dirs or [data_dir]
        files_to_combine = []
        for d in data_dirs:
            pattern = os.path.join(os.path.abspath(d), localdot)
            files_to_combine.extend(glob.glob(pattern))

        for f in files_to_combine:
            new_data = CoverageData()
            new_data.read_file(f)
            data.update(new_data, aliases=aliases)
            os.remove(f)
