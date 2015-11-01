# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

"""Helpers for coverage.py tests."""

import os
import subprocess
import sys

from coverage import env
from coverage.misc import output_encoding


def run_command(cmd):
    """Run a command in a sub-process.

    Returns the exit status code and the combined stdout and stderr.

    """
    if env.PY2 and isinstance(cmd, unicode):
        cmd = cmd.encode(sys.getfilesystemencoding())

    # In some strange cases (PyPy3 in a virtualenv!?) the stdout encoding of
    # the subprocess is set incorrectly to ascii.  Use an environment variable
    # to force the encoding to be the same as ours.
    sub_env = dict(os.environ)
    encoding = output_encoding()
    if encoding:
        sub_env['PYTHONIOENCODING'] = encoding

    proc = subprocess.Popen(
        cmd,
        shell=True,
        env=sub_env,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
        )
    output, _ = proc.communicate()
    status = proc.returncode

    # Get the output, and canonicalize it to strings with newlines.
    if not isinstance(output, str):
        output = output.decode(output_encoding())
    output = output.replace('\r', '')

    return status, output


class CheckUniqueFilenames(object):
    """Asserts the uniqueness of file names passed to a function."""
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
            "File name %r passed to %r twice" % (filename, self.wrapped)
            )
        self.filenames.add(filename)
        ret = self.wrapped(filename, *args, **kwargs)
        return ret
