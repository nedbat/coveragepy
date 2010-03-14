"""Add things to old Pythons so I can pretend they are newer, for tests."""

# pylint: disable-msg=W0622
# (Redefining built-in blah)
# The whole point of this file is to redefine built-ins, so shut up about it.

import os, sys

# Py2k and 3k don't agree on how to run commands in a subprocess.
try:
    import subprocess
except ImportError:
    def run_command(cmd):
        """Run a command in a subprocess.

        Returns the exit code and the combined stdout and stderr.

        """
        _, stdouterr = os.popen4(cmd)
        return 0, stdouterr.read()
else:
    def run_command(cmd):
        """Run a command in a subprocess.

        Returns the exit code and the combined stdout and stderr.

        """

        if sys.hexversion > 0x03000000 and cmd.startswith("coverage "):
            # We don't have a coverage command on 3.x, so fix it up to call the
            # script. Eventually we won't need this.
            script_path = os.path.join(sys.prefix, "Scripts", cmd)
            cmd = "python " + script_path

        proc = subprocess.Popen(cmd, shell=True,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
                )
        retcode = proc.wait()

        # Get the output, and canonicalize it to strings with newlines.
        output = proc.stdout.read()
        if not isinstance(output, str):
            output = output.decode('utf-8')
        output = output.replace('\r', '')

        return retcode, output

# No more execfile in Py3k
try:
    execfile = execfile
except NameError:
    def execfile(filename, globs):
        """A Python 3 implementation of execfile."""
        exec(compile(open(filename).read(), filename, 'exec'), globs)
