# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Helpers for coverage.py tests."""

import collections
import contextlib
import os
import os.path
import re
import shutil
import subprocess
import textwrap
import warnings

from unittest import mock

import pytest

from coverage import env
from coverage.exceptions import CoverageWarning
from coverage.misc import output_encoding


def run_command(cmd):
    """Run a command in a sub-process.

    Returns the exit status code and the combined stdout and stderr.

    """
    # Subprocesses are expensive, but convenient, and so may be over-used in
    # the test suite.  Use these lines to get a list of the tests using them:
    if 0:       # pragma: debugging
        with open("/tmp/processes.txt", "a") as proctxt:
            print(os.environ.get("PYTEST_CURRENT_TEST", "unknown"), file=proctxt, flush=True)

    # In some strange cases (PyPy3 in a virtualenv!?) the stdout encoding of
    # the subprocess is set incorrectly to ascii.  Use an environment variable
    # to force the encoding to be the same as ours.
    sub_env = dict(os.environ)
    sub_env['PYTHONIOENCODING'] = output_encoding()

    proc = subprocess.Popen(
        cmd,
        shell=True,
        env=sub_env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    output, _ = proc.communicate()
    status = proc.returncode

    # Get the output, and canonicalize it to strings with newlines.
    output = output.decode(output_encoding()).replace("\r", "")
    return status, output


def make_file(filename, text="", bytes=b"", newline=None):
    """Create a file for testing.

    `filename` is the relative path to the file, including directories if
    desired, which will be created if need be.

    `text` is the text content to create in the file, or `bytes` are the
    bytes to write.

    If `newline` is provided, it is a string that will be used as the line
    endings in the created file, otherwise the line endings are as provided
    in `text`.

    Returns `filename`.

    """
    # pylint: disable=redefined-builtin     # bytes
    if bytes:
        data = bytes
    else:
        text = textwrap.dedent(text)
        if newline:
            text = text.replace("\n", newline)
        data = text.encode("utf-8")

    # Make sure the directories are available.
    dirs, _ = os.path.split(filename)
    if dirs and not os.path.exists(dirs):
        os.makedirs(dirs)

    # Create the file.
    with open(filename, 'wb') as f:
        f.write(data)

    # For debugging, enable this to show the contents of files created.
    if 0:       # pragma: debugging
        print(f"   ───┬──┤ {filename} ├───────────────────────")
        for lineno, line in enumerate(data.splitlines(), start=1):
            print(f"{lineno:6}│ {line.rstrip().decode()}")
        print()

    return filename


def nice_file(*fparts):
    """Canonicalize the file name composed of the parts in `fparts`."""
    fname = os.path.join(*fparts)
    return os.path.normcase(os.path.abspath(os.path.realpath(fname)))


def os_sep(s):
    """Replace slashes in `s` with the correct separator for the OS."""
    return s.replace("/", os.sep)


class CheckUniqueFilenames:
    """Asserts the uniqueness of file names passed to a function."""
    def __init__(self, wrapped):
        self.filenames = set()
        self.wrapped = wrapped

    @classmethod
    def hook(cls, obj, method_name):
        """Replace a method with our checking wrapper.

        The method must take a string as a first argument. That argument
        will be checked for uniqueness across all the calls to this method.

        The values don't have to be file names actually, just strings, but
        we only use it for filename arguments.

        """
        method = getattr(obj, method_name)
        hook = cls(method)
        setattr(obj, method_name, hook.wrapper)
        return hook

    def wrapper(self, filename, *args, **kwargs):
        """The replacement method.  Check that we don't have dupes."""
        assert filename not in self.filenames, (
            f"File name {filename!r} passed to {self.wrapped!r} twice"
        )
        self.filenames.add(filename)
        ret = self.wrapped(filename, *args, **kwargs)
        return ret


def re_lines(pat, text, match=True):
    """Return a list of lines selected by `pat` in the string `text`.

    If `match` is false, the selection is inverted: only the non-matching
    lines are included.

    Returns a list, the selected lines, without line endings.

    """
    assert len(pat) < 200, "It's super-easy to swap the arguments to re_lines"
    return [l for l in text.splitlines() if bool(re.search(pat, l)) == match]


def re_lines_text(pat, text, match=True):
    """Return the multi-line text of lines selected by `pat`."""
    return "".join(l + "\n" for l in re_lines(pat, text, match=match))


def re_line(pat, text):
    """Return the one line in `text` that matches regex `pat`.

    Raises an AssertionError if more than one, or less than one, line matches.

    """
    lines = re_lines(pat, text)
    assert len(lines) == 1
    return lines[0]


def remove_tree(dirname):
    """Remove a directory tree.

    It's fine for the directory to not exist in the first place.
    """
    if os.path.exists(dirname):
        shutil.rmtree(dirname)


# Map chars to numbers for arcz_to_arcs
_arcz_map = {'.': -1}
_arcz_map.update({c: ord(c) - ord('0') for c in '123456789'})
_arcz_map.update({c: 10 + ord(c) - ord('A') for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'})

def arcz_to_arcs(arcz):
    """Convert a compact textual representation of arcs to a list of pairs.

    The text has space-separated pairs of letters.  Period is -1, 1-9 are
    1-9, A-Z are 10 through 36.  The resulting list is sorted regardless of
    the order of the input pairs.

    ".1 12 2." --> [(-1,1), (1,2), (2,-1)]

    Minus signs can be included in the pairs:

    "-11, 12, 2-5" --> [(-1,1), (1,2), (2,-5)]

    """
    arcs = []
    for pair in arcz.split():
        asgn = bsgn = 1
        if len(pair) == 2:
            a, b = pair
        else:
            assert len(pair) == 3
            if pair[0] == '-':
                _, a, b = pair
                asgn = -1
            else:
                assert pair[1] == '-'
                a, _, b = pair
                bsgn = -1
        arcs.append((asgn * _arcz_map[a], bsgn * _arcz_map[b]))
    return sorted(arcs)


_arcz_unmap = {val: ch for ch, val in _arcz_map.items()}

def _arcs_to_arcz_repr_one(num):
    """Return an arcz form of the number `num`, or "?" if there is none."""
    if num == -1:
        return "."
    z = ""
    if num < 0:
        z += "-"
        num *= -1
    z += _arcz_unmap.get(num, "?")
    return z


def arcs_to_arcz_repr(arcs):
    """Convert a list of arcs to a readable multi-line form for asserting.

    Each pair is on its own line, with a comment showing the arcz form,
    to make it easier to decode when debugging test failures.

    """
    repr_list = []
    for a, b in (arcs or ()):
        line = repr((a, b))
        line += " # "
        line += _arcs_to_arcz_repr_one(a)
        line += _arcs_to_arcz_repr_one(b)
        repr_list.append(line)
    return "\n".join(repr_list) + "\n"


@contextlib.contextmanager
def change_dir(new_dir):
    """Change directory, and then change back.

    Use as a context manager, it will return to the original
    directory at the end of the block.

    """
    old_dir = os.getcwd()
    os.chdir(str(new_dir))
    try:
        yield
    finally:
        os.chdir(old_dir)


def without_module(using_module, missing_module_name):
    """
    Hide a module for testing.

    Use this in a test function to make an optional module unavailable during
    the test::

        with without_module(product.something, 'tomli'):
            use_toml_somehow()

    Arguments:
        using_module: a module in which to hide `missing_module_name`.
        missing_module_name (str): the name of the module to hide.

    """
    return mock.patch.object(using_module, missing_module_name, None)


def assert_count_equal(a, b):
    """
    A pytest-friendly implementation of assertCountEqual.

    Assert that `a` and `b` have the same elements, but maybe in different order.
    This only works for hashable elements.
    """
    assert collections.Counter(list(a)) == collections.Counter(list(b))


def assert_coverage_warnings(warns, *msgs):
    """
    Assert that the CoverageWarning's in `warns` have `msgs` as messages.
    """
    assert msgs     # don't call this without some messages.
    warns = [w for w in warns if issubclass(w.category, CoverageWarning)]
    assert len(warns) == len(msgs)
    for actual, expected in zip((w.message.args[0] for w in warns), msgs):
        if hasattr(expected, "search"):
            assert expected.search(actual), f"{actual!r} didn't match {expected!r}"
        else:
            assert expected == actual


@contextlib.contextmanager
def swallow_warnings(message=r".", category=CoverageWarning):
    """Swallow particular warnings.

    It's OK if they happen, or if they don't happen. Just ignore them.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=category, message=message)
        yield


xfail_pypy_3749 = pytest.mark.xfail(
    env.PYVERSION[:2] == (3, 8) and env.PYPY and env.PYPYVERSION >= (7, 3, 10),
    reason="Avoid a PyPy bug: https://foss.heptapod.net/pypy/pypy/-/issues/3749",
)
