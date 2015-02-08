"""Helpers for coverage.py tests."""


class CheckUniqueFilenames(object):
    """Asserts the uniqueness of filenames passed to a function."""
    def __init__(self, wrapped):
        self.filenames = set()
        self.wrapped = wrapped

    @classmethod
    def hook(cls, cov, method_name):
        """Replace a method with our checking wrapper."""
        method = getattr(cov, method_name)
        hook = cls(method)
        setattr(cov, method_name, hook.wrapper)
        return hook

    def wrapper(self, filename, *args, **kwargs):
        """The replacement method.  Check that we don't have dupes."""
        assert filename not in self.filenames, (
            "Filename %r passed to %r twice" % (filename, self.wrapped)
            )
        self.filenames.add(filename)
        ret = self.wrapped(filename, *args, **kwargs)
        return ret
