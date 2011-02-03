"""Execute files of Python code."""

import imp, os, sys

from coverage.backward import exec_code_object, open_source
from coverage.misc import NoSource, ExceptionDuringRun


try:
    # In Py 2.x, the builtins were in __builtin__
    BUILTINS = sys.modules['__builtin__']
except KeyError:
    # In Py 3.x, they're in builtins
    BUILTINS = sys.modules['builtins']


def run_python_module(modulename, args):
    """Run a python module, as though with ``python -m name args...``.

    """
    # Search for the module - inside its parent package, if any - using
    # standard import mechanics.
    if '.' in modulename:
        packagename, name = modulename.rsplit('.')
        package = __import__(packagename, fromlist=['__path__'])
        searchpath = package.__path__
    else:
        packagename = None
        name = modulename
        searchpath = None  # means "top-level search" to find_module()
    openfile, pathname, description = imp.find_module(name, searchpath)

    # Complain if this is a magic non-file module.
    if openfile is None and pathname is None:
        raise NoSource("module does not live in a file: %r" % modulename)

    # If `modulename` is actually a package, not a mere module, then we
    # pretend to be Python 2.7 and try running its __main__.py script.
    if openfile is None:
        packagename = modulename
        name = '__main__'

        package = __import__(packagename, fromlist=['__path__'])
        searchpath = package.__path__
        openfile, pathname, description = imp.find_module(name, searchpath)

    # Finally, hand the file off to run_python_file for execution.
    openfile.close()
    run_python_file(pathname, args, package=packagename)


def run_python_file(filename, args, package=None):
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
    main_mod.__package__ = package
    main_mod.__builtins__ = BUILTINS

    # Set sys.argv and the first path element properly.
    old_argv = sys.argv
    old_path0 = sys.path[0]
    sys.argv = args
    sys.path[0] = os.path.dirname(filename)

    try:
        # Open the source file.
        try:
            source_file = open_source(filename)
        except IOError:
            raise NoSource("No file to run: %r" % filename)

        try:
            source = source_file.read()
        finally:
            source_file.close()

        # We have the source.  `compile` still needs the last line to be clean,
        # so make sure it is, then compile a code object from it.
        if source[-1] != '\n':
            source += '\n'
        code = compile(source, filename, "exec")

        # Execute the source file.
        try:
            exec_code_object(code, main_mod.__dict__)
        except SystemExit:
            # The user called sys.exit().  Just pass it along to the upper
            # layers, where it will be handled.
            raise
        except:
            # Something went wrong while executing the user code.
            # Get the exc_info, and pack them into an exception that we can
            # throw up to the outer loop.  We peel two layers off the traceback
            # so that the coverage.py code doesn't appear in the final printed
            # traceback.
            typ, err, tb = sys.exc_info()
            raise ExceptionDuringRun(typ, err, tb.tb_next.tb_next)
    finally:
        # Restore the old __main__
        sys.modules['__main__'] = old_main_mod

        # Restore the old argv and path
        sys.argv = old_argv
        sys.path[0] = old_path0
