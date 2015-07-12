"""Coverage data for Coverage."""

import glob
import os

from coverage.backward import iitems, pickle
from coverage.files import PathAliases
from coverage.misc import file_be_gone


class CoverageData(object):
    """Manages collected coverage data, including file storage.

    The data file format is a pickled dict, with these keys:

        * collector: a string identifying the collecting software

        * lines: a dict mapping filenames to sorted lists of line numbers
          executed::

            { 'file1': [17,23,45], 'file2': [1,2,3], ... }

        * arcs: a dict mapping filenames to sorted lists of line number pairs::

            { 'file1': [(17,23), (17,25), (25,26)], ... }

        * plugins: a dict mapping filenames to plugin names::

            { 'file1': "django.coverage", ... }

    """

    def __init__(self, collector=None, debug=None):
        """Create a CoverageData.

        `collector` is a string describing the coverage measurement software.

        `debug` is a `DebugControl` object for writing debug messages.

        """
        self.collector = collector
        self.debug = debug

        # A map from canonical Python source file name to a dictionary in
        # which there's an entry for each line number that has been
        # executed:
        #
        #   {
        #       'filename1.py': { 12: None, 47: None, ... },
        #       ...
        #       }
        #
        self.lines = {}

        # A map from canonical Python source file name to a dictionary with an
        # entry for each pair of line numbers forming an arc:
        #
        #   {
        #       'filename1.py': { (12,14): None, (47,48): None, ... },
        #       ...
        #       }
        #
        self.arcs = {}

        # A map from canonical source file name to a plugin module name:
        #
        #   {
        #       'filename1.py': 'django.coverage',
        #       ...
        #       }
        self.plugins = {}

    def erase(self):
        """Erase the data in this object."""
        self.lines = {}
        self.arcs = {}
        self.plugins = {}

    def line_data(self, filename):
        """Get the list of lines executed for a file."""
        return list(self.lines.get(filename, {}).keys())

    def plugin_name(self, filename):
        """Get the plugin name for a file.

        Arguments:
            filename: the name of the file you're interested in.

        Returns:
            str: the name of the plugin that handles this file.  Can be None
                if no plugin was involved.

        """
        return self.plugins.get(filename)

    def read(self, file_obj):
        """Return the stored coverage data from the given file.

        Returns three values, suitable for assigning to `self.lines`,
        `self.arcs`, and `self.plugins`.

        """
        self.lines = {}
        self.arcs = {}
        self.plugins = {}
        try:
            data = pickle.load(file_obj)
            if isinstance(data, dict):
                # Unpack the 'lines' item.
                self.lines = dict([
                    (f, dict.fromkeys(linenos, None))
                        for f, linenos in iitems(data.get('lines', {}))
                    ])
                # Unpack the 'arcs' item.
                self.arcs = dict([
                    (f, dict.fromkeys(arcpairs, None))
                        for f, arcpairs in iitems(data.get('arcs', {}))
                    ])
                self.plugins = data.get('plugins', {})
        except Exception:
            # TODO: this used to handle file-doesnt-exist problems.  Do we still need it?
            pass

    def read_file(self, filename):
        """Read the coverage data from `filename`."""
        if self.debug and self.debug.should('dataio'):
            self.debug.write("Reading data from %r" % (filename,))
        with open(filename, "rb") as f:
            self.read(f)

    def write(self, file_obj):
        """Write the coverage data to `file_obj`."""

        # Create the file data.
        file_data = {}

        file_data['lines'] = dict((f, list(lmap.keys())) for f, lmap in iitems(self.lines))

        if self.arcs:
            file_data['arcs'] = dict((f, list(amap.keys())) for f, amap in iitems(self.arcs))

        if self.collector:
            file_data['collector'] = self.collector

        file_data['plugins'] = self.plugins

        # Write the pickle to the file.
        pickle.dump(file_data, file_obj, 2)

    def write_file(self, filename):
        """Write the coverage data to `filename`."""
        if self.debug and self.debug.should('dataio'):
            self.debug.write("Writing data to %r" % (filename,))
        with open(filename, 'wb') as fdata:
            self.write(fdata)

    def add_line_data(self, line_data):
        """Add executed line data.

        `line_data` is { filename: { lineno: None, ... }, ...}

        """
        for filename, linenos in iitems(line_data):
            self.lines.setdefault(filename, {}).update(linenos)

    def add_arc_data(self, arc_data):
        """Add measured arc data.

        `arc_data` is { filename: { (l1,l2): None, ... }, ...}

        """
        for filename, arcs in iitems(arc_data):
            self.arcs.setdefault(filename, {}).update(arcs)

    def add_plugin_data(self, plugin_data):
        """Add per-file plugin information.

        `plugin_data` is { filename: plugin_name, ... }
        """
        self.plugins.update(plugin_data)

    def update(self, other_data, aliases=None):
        """
        If `aliases` is provided, it's a `PathAliases` object that is used to
        re-map paths to match the local machine's.

        """
        aliases = aliases or PathAliases()
        for filename, file_data in iitems(other_data.lines):
            filename = aliases.map(filename)
            self.lines.setdefault(filename, {}).update(file_data)
        for filename, file_data in iitems(other_data.arcs):
            filename = aliases.map(filename)
            self.arcs.setdefault(filename, {}).update(file_data)
        self.plugins.update(other_data.plugins)

    def touch_file(self, filename):
        """Ensure that `filename` appears in the data, empty if needed."""
        self.lines.setdefault(filename, {})

    def measured_files(self):
        """A list of all files that had been measured."""
        return list(self.lines.keys())

    def executed_lines(self, filename):
        """A map containing all the line numbers executed in `filename`.

        If `filename` hasn't been collected at all (because it wasn't executed)
        then return an empty map.

        """
        return self.lines.get(filename) or {}

    def executed_arcs(self, filename):
        """A map containing all the arcs executed in `filename`."""
        return self.arcs.get(filename) or {}

    def add_to_hash(self, filename, hasher):
        """Contribute `filename`'s data to the Md5Hash `hasher`."""
        hasher.update(self.executed_lines(filename))
        hasher.update(self.executed_arcs(filename))

    def summary(self, fullpath=False):
        """Return a dict summarizing the coverage data.

        Keys are based on the filenames, and values are the number of executed
        lines.  If `fullpath` is true, then the keys are the full pathnames of
        the files, otherwise they are the basenames of the files.

        """
        summ = {}
        if fullpath:
            filename_fn = lambda f: f
        else:
            filename_fn = os.path.basename
        for filename, lines in iitems(self.lines):
            summ[filename_fn(filename)] = len(lines)
        return summ

    def has_arcs(self):
        """Does this data have arcs?"""
        return bool(self.arcs)


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


if __name__ == '__main__':
    # Ad-hoc: show the raw data in a data file.
    import pprint, sys
    covdata = CoverageData()
    if sys.argv[1:]:
        fname = sys.argv[1]
    else:
        fname = covdata.filename
    pprint.pprint(covdata._raw_data(fname))
