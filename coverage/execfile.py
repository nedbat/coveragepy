"""Execute files of Python code."""

import os, sys

def run_python_file(filename):
    mod_globals = {
        '__name__': '__main__',
        '__file__': filename,
    }
    sys.path[0] = os.path.dirname(filename)
    execfile(filename, mod_globals)
