"""Add things to old Pythons so I can pretend they are newer."""

# pylint: disable-msg=W0622
# (Redefining built-in blah)
# The whole point of this file is to redefine built-ins, so shut up about it.

import os, sys

# Python 2.3 doesn't have `set`
try:
    set = set       # new in 2.4
except NameError:
    # (Redefining built-in 'set')
    from sets import Set as set


# Python 2.3 doesn't have `sorted`.
try:
    sorted = sorted
except NameError:
    def sorted(iterable):
        """A 2.3-compatible implementation of `sorted`."""
        lst = list(iterable)
        lst.sort()
        return lst

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
            # script.
            cmd = "python " + sys.prefix + os.sep + "Scripts" + os.sep + cmd

        proc = subprocess.Popen(cmd, shell=True,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
                )
        retcode = proc.wait()
        return retcode, proc.stdout.read()
