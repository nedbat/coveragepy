"""File wrangling."""

import os, sys

class FileLocator(object):
    """Understand how filenames work."""

    def __init__(self):
        self.relative_dir = self.abs_file(os.curdir) + os.sep

        # Cache of results of calling the canonical_filename() method, to
        # avoid duplicating work.
        self.canonical_filename_cache = {}

    def abs_file(self, filename):
        """Return the absolute normalized form of `filename`."""
        return os.path.normcase(os.path.abspath(os.path.realpath(filename)))

    def relative_filename(self, filename):
        """Return the relative form of `filename`.
        
        The filename will be relative to the current directory when the
        FileLocator was constructed.
        
        """
        return filename.replace(self.relative_dir, "")

    def canonical_filename(self, filename):
        """Return a canonical filename for `filename`.
        
        An absolute path with no redundant components and normalized case.
        
        """
        if filename not in self.canonical_filename_cache:
            f = filename
            if os.path.isabs(f) and not os.path.exists(f):
                if self.get_zip_data(f) is None:
                    f = os.path.basename(f)
            if not os.path.isabs(f):
                for path in [os.curdir] + sys.path:
                    g = os.path.join(path, f)
                    if os.path.exists(g):
                        f = g
                        break
            cf = self.abs_file(f)
            self.canonical_filename_cache[filename] = cf
        return self.canonical_filename_cache[filename]

    def get_zip_data(self, filename):
        """Get data from `filename` if it is a zip file path.
        
        Returns the string data read from the zip file, or None if no zip file
        could be found or `filename` isn't in it.  The data returned will be
        an empty string if the file is empty.
        
        """
        import zipimport
        markers = ['.zip'+os.sep, '.egg'+os.sep]
        for marker in markers:
            if marker in filename:
                parts = filename.split(marker)
                try:
                    zi = zipimport.zipimporter(parts[0]+marker[:-1])
                except zipimport.ZipImportError:
                    continue
                try:
                    data = zi.get_data(parts[1])
                except IOError:
                    continue
                if sys.hexversion > 0x03000000:
                    data = data.decode('utf8') # TODO: How to do this properly?
                return data
        return None
