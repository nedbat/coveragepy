"""Add things to old Pythons so I can pretend they are newer, for tests."""

# pylint: disable=W0622
# (Redefining built-in blah)
# The whole point of this file is to redefine built-ins, so shut up about it.

import os

# Py2k and 3k don't agree on how to run commands in a subprocess.
try:
    import subprocess
except ImportError:
    def run_command(cmd, status=0):
        """Run a command in a subprocess.

        Returns the exit status code and the combined stdout and stderr.

        """
        _, stdouterr = os.popen4(cmd)
        return status, stdouterr.read()

else:
    def run_command(cmd, status=0):
        """Run a command in a subprocess.

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

# No more execfile in Py3k
try:
    execfile = execfile
except NameError:
    def execfile(filename, globs):
        """A Python 3 implementation of execfile."""
        exec(compile(open(filename).read(), filename, 'exec'), globs)
