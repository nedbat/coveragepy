"""Add things to old Pythons so I can pretend they are newer."""

# This file does lots of tricky stuff, so disable a bunch of pylint warnings.
# pylint: disable=redefined-builtin
# pylint: disable=unused-import
# pylint: disable=no-name-in-module

import sys

from coverage import env


# Pythons 2 and 3 differ on where to get StringIO.
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

# What's a string called?
try:
    string_class = basestring
except NameError:
    string_class = str

# What's a Unicode string called?
try:
    unicode_class = unicode
except NameError:
    unicode_class = str

# Where do pickles come from?
try:
    import cPickle as pickle
except ImportError:
    import pickle

# range or xrange?
try:
    range = xrange
except NameError:
    range = range

# A function to iterate listlessly over a dict's items.
try:
    {}.iteritems
except AttributeError:
    def iitems(d):
        """Produce the items from dict `d`."""
        return d.items()
else:
    def iitems(d):
        """Produce the items from dict `d`."""
        return d.iteritems()

# Getting the `next` function from an iterator is different in 2 and 3.
try:
    iter([]).next
except AttributeError:
    def iternext(seq):
        """Get the `next` function for iterating over `seq`."""
        return iter(seq).__next__
else:
    def iternext(seq):
        """Get the `next` function for iterating over `seq`."""
        return iter(seq).next

# Python 3.x is picky about bytes and strings, so provide methods to
# get them right, and make them no-ops in 2.x
if env.PY3:
    def to_bytes(s):
        """Convert string `s` to bytes."""
        return s.encode('utf8')

    def binary_bytes(byte_values):
        """Produce a byte string with the ints from `byte_values`."""
        return bytes(byte_values)

    def byte_to_int(byte_value):
        """Turn an element of a bytes object into an int."""
        return byte_value

    def bytes_to_ints(bytes_value):
        """Turn a bytes object into a sequence of ints."""
        # In Python 3, iterating bytes gives ints.
        return bytes_value

else:
    def to_bytes(s):
        """Convert string `s` to bytes (no-op in 2.x)."""
        return s

    def binary_bytes(byte_values):
        """Produce a byte string with the ints from `byte_values`."""
        return "".join(chr(b) for b in byte_values)

    def byte_to_int(byte_value):
        """Turn an element of a bytes object into an int."""
        return ord(byte_value)

    def bytes_to_ints(bytes_value):
        """Turn a bytes object into a sequence of ints."""
        for byte in bytes_value:
            yield ord(byte)


try:
    # In Python 2.x, the builtins were in __builtin__
    BUILTINS = sys.modules['__builtin__']
except KeyError:
    # In Python 3.x, they're in builtins
    BUILTINS = sys.modules['builtins']


# imp was deprecated in Python 3.3
try:
    import importlib
    import importlib.util
    imp = None
except ImportError:
    importlib = None

# We only want to use importlib if it has everything we need.
try:
    importlib_util_find_spec = importlib.util.find_spec
except Exception:
    import imp
    importlib_util_find_spec = None

# What is the .pyc magic number for this version of Python?
try:
    PYC_MAGIC_NUMBER = importlib.util.MAGIC_NUMBER
except AttributeError:
    PYC_MAGIC_NUMBER = imp.get_magic()


def import_local_file(modname):
    """Import a local file as a module.

    Opens a file in the current directory named `modname`.py, imports it
    as `modname`, and returns the module object.

    """
    try:
        from importlib.machinery import SourceFileLoader
    except ImportError:
        SourceFileLoader = None

    modfile = modname + '.py'
    if SourceFileLoader:
        mod = SourceFileLoader(modname, modfile).load_module()
    else:
        for suff in imp.get_suffixes():                 # pragma: part covered
            if suff[0] == '.py':
                break

        with open(modfile, 'r') as f:
            # pylint: disable=undefined-loop-variable
            # (Using possibly undefined loop variable 'suff')
            mod = imp.load_module(modname, f, modfile, suff)

    return mod
