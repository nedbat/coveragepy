"""Execute files of Python code."""

import imp, os, sys

from coverage.backward import exec_function
from coverage.misc import NoSource


try:
    # In Py 2.x, the builtins were in __builtin__
    BUILTINS = sys.modules['__builtin__']
except KeyError:
    # In Py 3.x, they're in builtins
    BUILTINS = sys.modules['builtins']


def run_python_file(filename, args):
    """Run a python file as if it were the main program on the command line.
    
    `filename` is the path to the file to execute, it need not be a .py file.
    `args` is the argument array to present as sys.argv, including the first
    element representing the file being executed.
    
    """
    # Create a module to serve as __main__
    old_main_mod = sys.modules['__main__']
    main_mod = imp.new_module('__main__')
    sys.modules['__main__'] = main_mod
    main_mod.__file__ = filename
    main_mod.__builtins__ = BUILTINS

    # Set sys.argv and the first path element properly.
    old_argv = sys.argv
    old_path0 = sys.path[0]
    sys.argv = args
    sys.path[0] = os.path.dirname(filename)

    try:
        try:
            source = open(filename, 'rU').read()
        except IOError:
            raise NoSource("No file to run: %r" % filename)
        exec_function(source, filename, main_mod.__dict__)
    finally:
        # Restore the old __main__
        sys.modules['__main__'] = old_main_mod
        
        # Restore the old argv and path
        sys.argv = old_argv
        sys.path[0] = old_path0
