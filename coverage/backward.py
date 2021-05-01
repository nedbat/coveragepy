# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Add things to old Pythons so I can pretend they are newer."""

import sys

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


def code_object(fn):
    """Get the code object from a function."""
    try:
        return fn.func_code
    except AttributeError:
        return fn.__code__


try:
    from types import SimpleNamespace
except ImportError:
    # The code from https://docs.python.org/3/library/types.html#types.SimpleNamespace
    class SimpleNamespace:
        """Python implementation of SimpleNamespace, for Python 2."""
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

        def __repr__(self):
            keys = sorted(self.__dict__)
            items = ("{}={!r}".format(k, self.__dict__[k]) for k in keys)
            return "{}({})".format(type(self).__name__, ", ".join(items))


def format_local_datetime(dt):
    """Return a string with local timezone representing the date.
    If python version is lower than 3.6, the time zone is not included.
    """
    try:
        return dt.astimezone().strftime('%Y-%m-%d %H:%M %z')
    except (TypeError, ValueError):
        # Datetime.astimezone in Python 3.5 can not handle naive datetime
        return dt.strftime('%Y-%m-%d %H:%M')


def import_local_file(modname, modfile=None):
    """Import a local file as a module.

    Opens a file in the current directory named `modname`.py, imports it
    as `modname`, and returns the module object.  `modfile` is the file to
    import if it isn't in the current directory.

    """
    try:
        import importlib.util as importlib_util
    except ImportError:
        importlib_util = None

    if modfile is None:
        modfile = modname + '.py'
    if importlib_util:
        spec = importlib_util.spec_from_file_location(modname, modfile)
        mod = importlib_util.module_from_spec(spec)
        sys.modules[modname] = mod
        spec.loader.exec_module(mod)
    else:
        for suff in imp.get_suffixes():                 # pragma: part covered
            if suff[0] == '.py':
                break

        with open(modfile, 'r') as f:
            # pylint: disable=undefined-loop-variable
            mod = imp.load_module(modname, f, modfile, suff)

    return mod
