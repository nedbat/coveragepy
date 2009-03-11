"""Code unit (module) handling for coverage.py"""

import glob, os, types

def code_unit_factory(morfs, file_wrangler, omit_prefixes=None):
    """Construct a list of CodeUnits from polymorphic inputs.
    
    `morfs` is a module or a filename, or a list of same.
    `file_wrangler` is a FileWrangler that can help resolve filenames.
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

    code_units = [CodeUnit(morf, file_wrangler) for morf in morfs]
    
    if omit_prefixes:
        prefixes = [file_wrangler.abs_file(p) for p in omit_prefixes]
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
    
    `name` is a human-readable name for this code unit.
    `filename` is the os path from which we can read the source.
    
    """

    def __init__(self, morf, file_wrangler):
        if hasattr(morf, '__file__'):
            f = morf.__file__
        else:
            f = morf
        self.filename = file_wrangler.canonical_filename(f)

        if hasattr(morf, '__name__'):
            n = morf.__name__
        else:
            n = os.path.splitext(morf)[0]
            n = file_wrangler.relative_filename(n)
        self.name = n

    def __cmp__(self, other):
        return cmp(self.name, other.name)
