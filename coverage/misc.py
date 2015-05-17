"""Miscellaneous stuff for Coverage."""

import errno
import hashlib
import inspect
import os

from coverage import env
from coverage.backward import string_class, to_bytes, unicode_class


# Use PyContracts for assertion testing on parameters and returns, but only if
# we are running our own test suite.
contract = None

if env.TESTING:
    try:
        from contracts import contract
    except ImportError:
        pass
    else:
        from contracts import new_contract

        # Define contract words that PyContract doesn't have.
        new_contract('bytes', lambda v: isinstance(v, bytes))
        if env.PY3:
            new_contract('unicode', lambda v: isinstance(v, unicode_class))

if not contract:
    # We aren't using real PyContracts, so just define a no-op decorator as a
    # stunt double.
    def contract(**unused):             # pylint: disable=function-redefined
        """Dummy no-op implementation of `contract`."""
        return lambda func: func


def nice_pair(pair):
    """Make a nice string representation of a pair of numbers.

    If the numbers are equal, just return the number, otherwise return the pair
    with a dash between them, indicating the range.

    """
    start, end = pair
    if start == end:
        return "%d" % start
    else:
        return "%d-%d" % (start, end)


def format_lines(statements, lines):
    """Nicely format a list of line numbers.

    Format a list of line numbers for printing by coalescing groups of lines as
    long as the lines represent consecutive statements.  This will coalesce
    even if there are gaps between statements.

    For example, if `statements` is [1,2,3,4,5,10,11,12,13,14] and
    `lines` is [1,2,5,10,11,13,14] then the result will be "1-2, 5-11, 13-14".

    """
    pairs = []
    i = 0
    j = 0
    start = None
    statements = sorted(statements)
    lines = sorted(lines)
    while i < len(statements) and j < len(lines):
        if statements[i] == lines[j]:
            if start is None:
                start = lines[j]
            end = lines[j]
            j += 1
        elif start:
            pairs.append((start, end))
            start = None
        i += 1
    if start:
        pairs.append((start, end))
    ret = ', '.join(map(nice_pair, pairs))
    return ret


def short_stack():                                          # pragma: debugging
    """Return a string summarizing the call stack."""
    stack = inspect.stack()[:0:-1]
    return "\n".join("%30s : %s @%d" % (t[3], t[1], t[2]) for t in stack)


def expensive(fn):
    """A decorator to cache the result of an expensive operation.

    Only applies to methods with no arguments.

    """
    attr = "_cache_" + fn.__name__

    def _wrapped(self):
        """Inner fn that checks the cache."""
        if not hasattr(self, attr):
            setattr(self, attr, fn(self))
        return getattr(self, attr)
    return _wrapped


def bool_or_none(b):
    """Return bool(b), but preserve None."""
    if b is None:
        return None
    else:
        return bool(b)


def join_regex(regexes):
    """Combine a list of regexes into one that matches any of them."""
    return "|".join("(?:%s)" % r for r in regexes)


def file_be_gone(path):
    """Remove a file, and don't get annoyed if it doesn't exist."""
    try:
        os.remove(path)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


class Hasher(object):
    """Hashes Python data into md5."""
    def __init__(self):
        self.md5 = hashlib.md5()

    def update(self, v):
        """Add `v` to the hash, recursively if needed."""
        self.md5.update(to_bytes(str(type(v))))
        if isinstance(v, string_class):
            self.md5.update(to_bytes(v))
        elif isinstance(v, bytes):
            self.md5.update(v)
        elif v is None:
            pass
        elif isinstance(v, (int, float)):
            self.md5.update(to_bytes(str(v)))
        elif isinstance(v, (tuple, list)):
            for e in v:
                self.update(e)
        elif isinstance(v, dict):
            keys = v.keys()
            for k in sorted(keys):
                self.update(k)
                self.update(v[k])
        else:
            for k in dir(v):
                if k.startswith('__'):
                    continue
                a = getattr(v, k)
                if inspect.isroutine(a):
                    continue
                self.update(k)
                self.update(a)

    def hexdigest(self):
        """Retrieve the hex digest of the hash."""
        return self.md5.hexdigest()


def overrides(obj, method_name, base_class):
    """Does `obj` override the `method_name` it got from `base_class`?

    Determine if `obj` implements the method called `method_name`, which it
    inherited from `base_class`.

    Returns a boolean.

    """
    klass = obj.__class__
    klass_func = getattr(klass, method_name)
    base_func = getattr(base_class, method_name)

    # Python 2/3 compatibility: Python 2 returns an instancemethod object, the
    # function is the .im_func attribute.  Python 3 returns a plain function
    # object already.
    if env.PY2:
        klass_func = klass_func.im_func
        base_func = base_func.im_func

    return klass_func is not base_func


# TODO: abc?
def _needs_to_implement(that, func_name):
    """Helper to raise NotImplementedError in interface stubs."""
    if hasattr(that, "_coverage_plugin_name"):
        thing = "Plugin"
        name = that._coverage_plugin_name
    else:
        thing = "Class"
        klass = that.__class__
        name = "{klass.__module__}.{klass.__name__}".format(klass=klass)

    raise NotImplementedError(
        "{thing} {name!r} needs to implement {func_name}()".format(
            thing=thing, name=name, func_name=func_name
            )
        )


class CoverageException(Exception):
    """An exception specific to Coverage."""
    pass


class NoSource(CoverageException):
    """We couldn't find the source for a module."""
    pass


class NoCode(NoSource):
    """We couldn't find any code at all."""
    pass


class NotPython(CoverageException):
    """A source file turned out not to be parsable Python."""
    pass


class ExceptionDuringRun(CoverageException):
    """An exception happened while running customer code.

    Construct it with three arguments, the values from `sys.exc_info`.

    """
    pass
