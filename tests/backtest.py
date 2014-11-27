"""Add things to old Pythons so I can pretend they are newer, for tests."""

# pylint: disable=redefined-builtin
# (Redefining built-in blah)
# The whole point of this file is to redefine built-ins, so shut up about it.

import subprocess


# This isn't really a backward compatibility thing, should be moved into a
# helpers file or something.
def run_command(cmd):
    """Run a command in a sub-process.

    Returns the exit status code and the combined stdout and stderr.

    """
    proc = subprocess.Popen(cmd, shell=True,
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


# No more execfile in Py3
try:
    execfile = execfile
except NameError:
    def execfile(filename, globs):
        """A Python 3 implementation of execfile."""
        with open(filename) as fobj:
            code = fobj.read()
        exec(compile(code, filename, 'exec'), globs)
