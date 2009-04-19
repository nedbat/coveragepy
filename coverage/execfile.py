"""Execute files of Python code."""

import imp, os, sys

def run_python_file(filename, args):
    """Run a python source file as if it were the main program on the python
    command line.
    
    `filename` is the path to the file to execute, must be a .py file.
    `args` is the argument array to present as sys.argv.
    
    """
    # Most code that does this does it in a way that leaves __main__ or
    # __file__ with the wrong values.  Importing the code as __main__ gets all
    # of this right automatically.
    #
    # One difference from python.exe: if I run foo.py from the command line, it
    # always uses foo.py.  With this code, it might find foo.pyc instead.
    
    sys.argv = args
    sys.path[0] = os.path.dirname(filename)

    src = open(filename)
    try:
        imp.load_module('__main__', src, filename, (".py", "r", imp.PY_SOURCE))
    finally:
        src.close()
