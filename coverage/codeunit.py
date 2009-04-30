"""Code unit (module) handling for Coverage."""

import glob, os, types

def code_unit_factory(morfs, file_locator, omit_prefixes=None):
    """Construct a list of CodeUnits from polymorphic inputs.
    
    `morfs` is a module or a filename, or a list of same.
    `file_locator` is a FileLocator that can help resolve filenames.
    `omit_prefixes` is a list of prefixes.  CodeUnits that match those prefixes
    will be omitted from the list.
    
    Returns a list of CodeUnit objects.
    
    """

    # Be sure we have a list.
    if not isinstance(morfs, types.ListType):
        morfs = [morfs]
    
    # On Windows, the shell doesn't expand wildcards.  Do it here.
    globbed = []
    for morf in morfs:
        if isinstance(morf, basestring) and ('?' in morf or '*' in morf):
            globbed.extend(glob.glob(morf))
        else:
            globbed.append(morf)
    morfs = globbed

    code_units = [CodeUnit(morf, file_locator) for morf in morfs]
    
    if omit_prefixes:
        prefixes = [file_locator.abs_file(p) for p in omit_prefixes]
        filtered = []
        for cu in code_units:
            for prefix in prefixes:
                if cu.name.startswith(prefix):
                    break
            else:
                filtered.append(cu)
    
        code_units = filtered

    return code_units


class CodeUnit:
    """Code unit: a filename or module.
    
    Instance attributes:
    
    `name` is a human-readable name for this code unit.
    `filename` is the os path from which we can read the source.
    `relative` is a boolean.
    
    """

    def __init__(self, morf, file_locator):
        if hasattr(morf, '__file__'):
            f = morf.__file__
        else:
            f = morf
        # .pyc files should always refer to a .py instead.
        if f.endswith('.pyc'):
            f = f[:-1]
        self.filename = file_locator.canonical_filename(f)

        if hasattr(morf, '__name__'):
            n = morf.__name__
            self.relative = True
        else:
            n = os.path.splitext(morf)[0]
            rel = file_locator.relative_filename(n)
            if os.path.isabs(n):
                self.relative = (rel != n)
            else:
                self.relative = True
            n = rel
        self.name = n

    def __repr__(self):
        return "<CodeUnit name=%r filename=%r>" % (self.name, self.filename)

    def __cmp__(self, other):
        return cmp(self.name, other.name)

    def flat_rootname(self):
        """A base for a flat filename to correspond to this code unit.
        
        Useful for writing files about the code where you want all the files in
        the same directory, but need to differentiate same-named files from
        different directories.
        
        For example, the file a/b/c.py might return 'a_b_c'
        
        """
        root = os.path.splitdrive(os.path.splitext(self.name)[0])[1]
        return root.replace('\\', '_').replace('/', '_')

    def source_file(self):
        """Return an open file for reading the source of the code unit."""
        return open(self.filename)
