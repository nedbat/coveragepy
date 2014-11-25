"""Test file for run_python_file.

This file is executed two ways::

    $ coverage run try_execfile.py

and::

    $ python try_execfile.py

The output is compared to see that the program execution context is the same
under coverage and under Python.

It is not crucial that the execution be identical, there are some differences
that are OK.  This program canonicalizes the output to gloss over those
differences and get a clean diff.

"""

import json, os, sys

# sys.path varies by execution environments.  Coverage.py uses setuptools to
# make console scripts, which means pkg_resources is imported.  pkg_resources
# removes duplicate entries from sys.path.  So we do that too, since the extra
# entries don't affect the running of the program.

def same_file(p1, p2):
    """Determine if `p1` and `p2` refer to the same existing file."""
    if not p1:
        return not p2
    if not os.path.exists(p1):
        return False
    if not os.path.exists(p2):
        return False
    return os.path.samefile(p1, p2)

def without_same_files(filenames):
    """Return the list `filenames` with duplicates (by same_file) removed."""
    reduced = []
    for filename in filenames:
        if not any(same_file(filename, other) for other in reduced):
            reduced.append(filename)
    return reduced

cleaned_sys_path = [os.path.normcase(p) for p in without_same_files(sys.path)]

DATA = "xyzzy"

import __main__

def my_function(a):
    """A function to force execution of module-level values."""
    return "my_fn(%r)" % a

FN_VAL = my_function("fooey")

loader = globals().get('__loader__')
fullname = getattr(loader, 'fullname', None) or getattr(loader, 'name', None)

globals_to_check = {
    '__name__': __name__,
    '__file__': __file__,
    '__doc__': __doc__,
    '__builtins__.has_open': hasattr(__builtins__, 'open'),
    '__builtins__.dir': dir(__builtins__),
    '__loader__ exists': loader is not None,
    '__loader__.fullname': fullname,
    '__package__': __package__,
    'DATA': DATA,
    'FN_VAL': FN_VAL,
    '__main__.DATA': getattr(__main__, "DATA", "nothing"),
    'argv': sys.argv,
    'path': cleaned_sys_path,
}

print(json.dumps(globals_to_check, indent=4, sort_keys=True))
