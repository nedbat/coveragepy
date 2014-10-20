"""Test file for run_python_file."""

import os, pprint, sys

DATA = "xyzzy"

import __main__

def my_function(a):
    """A function to force execution of module-level values."""
    return "my_fn(%r)" % a

FN_VAL = my_function("fooey")

globals_to_check = {
    '__name__': __name__,
    '__file__': __file__,
    '__doc__': __doc__,
    '__builtins__.has_open': hasattr(__builtins__, 'open'),
    '__builtins__.dir': dir(__builtins__),
    '__package__': __package__,
    'DATA': DATA,
    'FN_VAL': FN_VAL,
    '__main__.DATA': getattr(__main__, "DATA", "nothing"),
    'argv': sys.argv,
    'path': [os.path.normcase(p) for p in sys.path],
}

pprint.pprint(globals_to_check)
