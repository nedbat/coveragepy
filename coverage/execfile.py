"""Execute files of Python code."""

import imp, os, sys

try:
    # In Py 2.x, the builtins were in __builtin__
    BUILTINS = sys.modules['__builtin__']
except KeyError:
    # In Py 3.x, they're in builtin
    BUILTINS = sys.modules['builtin']


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
        source = open(filename, 'rU').read()
        exec compile(source, filename, "exec") in main_mod.__dict__
    finally:
        # Restore the old __main__
        sys.modules['__main__'] = old_main_mod
        
        # Restore the old argv and path
        sys.argv = old_argv
        sys.path[0] = old_path0
