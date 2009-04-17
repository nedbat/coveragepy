"""Coverage data for coverage.py"""

import os, types
import cPickle as pickle

class CoverageData:
    """Manages collected coverage data."""
    # Name of the data file (unless environment variable is set).
    filename_default = ".coverage"

    # Environment variable naming the data file.
    filename_env = "COVERAGE_FILE"

    def __init__(self):
        self.use_file = True
        self.filename = None
        self.suffix = None

        # A map from canonical Python source file name to a dictionary in
        # which there's an entry for each line number that has been
        # executed:
        #
        #   {
        #       'filename1.py': { 12: True, 47: True, ... },
        #       ...
        #       }
        #
        self.executed = {}
        
    def usefile(self, use_file=True):
        """Set whether or not to use a disk file for data."""
        self.use_file = use_file

    def set_suffix(self, suffix):
        """Set a suffix to use for the data file name.
        
        This can be used for multiple or parallel execution, so that many
        coverage data files can exist simultaneously.
        
        """
        self.suffix = suffix

    def _make_filename(self):
        if not self.filename:
            self.filename = os.environ.get(
                                    self.filename_env, self.filename_default)
            if self.suffix:
                self.filename += "." + self.suffix

    def read(self):
        """Read coverage data from the coverage data file (if it exists)."""
        data = {}
        if self.use_file:
            self._make_filename()
            data = self._read_file(self.filename)
        self.executed = data

    def write(self):
        """Write the collected coverage data to a file."""
        if self.use_file:
            self._make_filename()
            self.write_file(self.filename)

    def erase(self):
        if self.filename and os.path.exists(self.filename):
            os.remove(self.filename)

    def write_file(self, filename):
        """Write the coverage data to `filename`."""
        f = open(filename, 'wb')
        try:
            pickle.dump(self.executed, f)
        finally:
            f.close()

    def read_file(self, filename):
        self.executed = self._read_file(filename)

    def _read_file(self, filename):
        """ Return the stored coverage data from the given file.
        """
        try:
            fdata = open(filename, 'rb')
            try:
                executed = pickle.load(fdata)
            finally:
                fdata.close()
            if isinstance(executed, types.DictType):
                return executed
            else:
                return {}
        except:
            return {}

    def combine_parallel_data(self):
        """ Treat self.filename as a file prefix, and combine the data from all
            of the files starting with that prefix.
        """
        data_dir, local = os.path.split(self.filename)
        for f in os.listdir(data_dir or '.'):
            if f.startswith(local):
                full_path = os.path.join(data_dir, f)
                file_data = self._read_file(full_path)
                self._combine_data(file_data)

    def _combine_data(self, new_data):
        """Combine the `new_data` into `executed`."""
        for filename, file_data in new_data.items():
            self.executed.setdefault(filename, {}).update(file_data)

    def add_line_data(self, data_points):
        """Add executed line data.
        
        `data_points` is (filename, lineno) pairs.
        
        """
        for filename, lineno in data_points:
            self.executed.setdefault(filename, {})[lineno] = True

    def executed_files(self):
        """A list of all files that had been measured as executed."""
        return self.executed.keys()

    def executed_lines(self, filename):
        """A map containing all the line numbers executed in `filename`.
        
        If `filename` hasn't been collected at all (because it wasn't executed)
        then return an empty map.
        """
        return self.executed.get(filename) or {}

    def summary(self):
        """Return a dict summarizing the coverage data.
        
        Keys are the basename of the filenames, and values are the number of
        executed lines.  This is useful in the unit tests.
        
        """
        summ = {}
        for filename, lines in self.executed.items():
            summ[os.path.basename(filename)] = len(lines)
        return summ
