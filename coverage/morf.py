"""Module or Filename handling for coverage.py"""

# TODO: Distinguish between morf (input: module or filename), and Morf (class
# that can represent either).

def morf_factory(morfs, omit_prefixes=None):
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

    morfs = map(Morf, morfs)
    
    if omit_prefixes:
        filtered_morfs = []
        for morf in morfs:
            for prefix in omit_prefixes:
                if morf.name.startswith(prefix):
                    break
            else:
                filtered_morfs.append(morf)
    
        morfs = filtered_morfs

    return morfs

class Morf:
    def __init__(self, morf):
        if hasattr(morf, '__file__'):
            f = morf.__file__
        else:
            f = morf
        self.filename = self.canonical_filename(f)

        if hasattr(morf, '__name__'):
            self.name = morf.__name__
        else:
            self.name = self.relative_filename(os.path.splitext(morf)[0])

    def __cmp__(self, other):
        return cmp(self.name, other.name)
