"""Helpers for coverage.py tests."""

import subprocess


# This isn't really a backward compatibility thing, should be moved into a
# helpers file or something.
def run_command(cmd):
    """Run a command in a sub-process.

    Returns the exit status code and the combined stdout and stderr.

    """
    proc = subprocess.Popen(
        cmd, shell=True,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
        )
    output, _ = proc.communicate()
    status = proc.returncode

    # Get the output, and canonicalize it to strings with newlines.
    if not isinstance(output, str):
        output = output.decode('utf-8')
    output = output.replace('\r', '')

    return status, output


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
