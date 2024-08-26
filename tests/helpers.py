# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Helpers for coverage.py tests."""

from __future__ import annotations

import collections
import contextlib
import dis
import io
import locale
import os
import os.path
import re
import shutil
import subprocess
import textwrap
import warnings

from pathlib import Path
from typing import (
    Any, Callable, Iterable, Iterator, NoReturn, TypeVar, cast,
)

import flaky
import pytest

from coverage import env
from coverage.debug import DebugControl
from coverage.exceptions import CoverageWarning
from coverage.types import TArc


def run_command(cmd: str) -> tuple[int, str]:
    """Run a command in a sub-process.

    Returns the exit status code and the combined stdout and stderr.

    """
    # Subprocesses are expensive, but convenient, and so may be over-used in
    # the test suite.  Use these lines to get a list of the tests using them:
    if 0:  # pragma: debugging
        with open("/tmp/processes.txt", "a") as proctxt:  # type: ignore[unreachable]
            print(os.getenv("PYTEST_CURRENT_TEST", "unknown"), file=proctxt, flush=True)

    encoding = os.device_encoding(1) or locale.getpreferredencoding()

    # In some strange cases (PyPy3 in a virtualenv!?) the stdout encoding of
    # the subprocess is set incorrectly to ascii.  Use an environment variable
    # to force the encoding to be the same as ours.
    sub_env = dict(os.environ)
    sub_env['PYTHONIOENCODING'] = encoding

    proc = subprocess.Popen(
        cmd,
        shell=True,
        env=sub_env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    output, _ = proc.communicate()
    status = proc.returncode

    # Get the output, and canonicalize it to strings with newlines.
    output_str = output.decode(encoding).replace("\r", "")
    return status, output_str


# $set_env.py: COVERAGE_DIS - Disassemble test code to /tmp/dis
SHOW_DIS = bool(int(os.getenv("COVERAGE_DIS", "0")))

def make_file(
    filename: str,
    text: str = "",
    bytes: bytes = b"",
    newline: str | None = None,
) -> str:
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
    dirs, basename = os.path.split(filename)
    if dirs:
        os.makedirs(dirs, exist_ok=True)

    # Create the file.
    with open(filename, 'wb') as f:
        f.write(data)

    if text and basename.endswith(".py") and SHOW_DIS:      # pragma: debugging
        os.makedirs("/tmp/dis", exist_ok=True)
        with open(f"/tmp/dis/{basename}.dis", "w") as fdis:
            print(f"# {os.path.abspath(filename)}", file=fdis)
            cur_test = os.getenv("PYTEST_CURRENT_TEST", "unknown")
            print(f"# PYTEST_CURRENT_TEST = {cur_test}", file=fdis)
            kwargs = {}
            if env.PYVERSION >= (3, 13):
                kwargs["show_offsets"] = True
            try:
                dis.dis(text, file=fdis, **kwargs)
            except Exception as exc:
                # Some tests make .py files that aren't Python, so dis will
                # fail, which is expected.
                print(f"#! {exc!r}", file=fdis)

    # For debugging, enable this to show the contents of files created.
    if 0:  # pragma: debugging
        print(f"   ───┬──┤ {filename} ├───────────────────────")  # type: ignore[unreachable]
        for lineno, line in enumerate(data.splitlines(), start=1):
            print(f"{lineno:6}│ {line.rstrip().decode()}")
        print()

    return filename


def nice_file(*fparts: str) -> str:
    """Canonicalize the file name composed of the parts in `fparts`."""
    fname = os.path.join(*fparts)
    return os.path.normcase(os.path.abspath(os.path.realpath(fname)))


def os_sep(s: str) -> str:
    """Replace slashes in `s` with the correct separator for the OS."""
    return s.replace("/", os.sep)


class CheckUniqueFilenames:
    """Asserts the uniqueness of file names passed to a function."""

    def __init__(self, wrapped: Callable[..., Any]) -> None:
        self.filenames: set[str] = set()
        self.wrapped = wrapped

    @classmethod
    def hook(cls, obj: Any, method_name: str) -> CheckUniqueFilenames:
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

    def wrapper(self, filename: str, *args: Any, **kwargs: Any) -> Any:
        """The replacement method.  Check that we don't have dupes."""
        assert filename not in self.filenames, (
            f"File name {filename!r} passed to {self.wrapped!r} twice"
        )
        self.filenames.add(filename)
        return self.wrapped(filename, *args, **kwargs)


def re_lines(pat: str, text: str, match: bool = True) -> list[str]:
    """Return a list of lines selected by `pat` in the string `text`.

    If `match` is false, the selection is inverted: only the non-matching
    lines are included.

    Returns a list, the selected lines, without line endings.

    """
    assert len(pat) < 200, "It's super-easy to swap the arguments to re_lines"
    return [l for l in text.splitlines() if bool(re.search(pat, l)) == match]


def re_lines_text(pat: str, text: str, match: bool = True) -> str:
    """Return the multi-line text of lines selected by `pat`."""
    return "".join(l + "\n" for l in re_lines(pat, text, match=match))


def re_line(pat: str, text: str) -> str:
    """Return the one line in `text` that matches regex `pat`.

    Raises an AssertionError if more than one, or less than one, line matches.

    """
    lines = re_lines(pat, text)
    assert len(lines) == 1
    return lines[0]


def remove_tree(dirname: str) -> None:
    """Remove a directory tree.

    It's fine for the directory to not exist in the first place.
    """
    if os.path.exists(dirname):
        shutil.rmtree(dirname)


# Map chars to numbers for arcz_to_arcs
_arcz_map = {'.': -1}
_arcz_map.update({c: ord(c) - ord('0') for c in '123456789'})
_arcz_map.update({c: 10 + ord(c) - ord('A') for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'})


def arcz_to_arcs(arcz: str) -> list[TArc]:
    """Convert a compact textual representation of arcs to a list of pairs.

    The text has space-separated pairs of letters.  Period is -1, 1-9 are
    1-9, A-Z are 10 through 36.  The resulting list is sorted regardless of
    the order of the input pairs.

    ".1 12 2." --> [(-1,1), (1,2), (2,-1)]

    Minus signs can be included in the pairs:

    "-11, 12, 2-5" --> [(-1,1), (1,2), (2,-5)]

    """
    # The `type: ignore[misc]` here are to suppress "Unpacking a string is
    # disallowed".
    a: str
    b: str
    arcs = []
    for pair in arcz.split():
        asgn = bsgn = 1
        if len(pair) == 2:
            a, b = pair                 # type: ignore[misc]
        else:
            assert len(pair) == 3
            if pair[0] == "-":
                _, a, b = pair          # type: ignore[misc]
                asgn = -1
            else:
                assert pair[1] == "-"
                a, _, b = pair          # type: ignore[misc]
                bsgn = -1
        arcs.append((asgn * _arcz_map[a], bsgn * _arcz_map[b]))
    return sorted(arcs)


@contextlib.contextmanager
def change_dir(new_dir: str | Path) -> Iterator[None]:
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

T = TypeVar("T")

def assert_count_equal(
    a: Iterable[T] | None,
    b: Iterable[T] | None,
) -> None:
    """
    A pytest-friendly implementation of assertCountEqual.

    Assert that `a` and `b` have the same elements, but maybe in different order.
    This only works for hashable elements.
    """
    assert a is not None
    assert b is not None
    assert collections.Counter(list(a)) == collections.Counter(list(b))


def assert_coverage_warnings(
    warns: Iterable[warnings.WarningMessage],
    *msgs: str | re.Pattern[str],
) -> None:
    """
    Assert that the CoverageWarning's in `warns` have `msgs` as messages.

    Each msg can be a string compared for equality, or a compiled regex used to
    search the text.
    """
    assert msgs     # don't call this without some messages.
    warns = [w for w in warns if issubclass(w.category, CoverageWarning)]
    actuals = [cast(Warning, w.message).args[0] for w in warns]
    assert len(msgs) == len(actuals)
    for expected, actual in zip(msgs, actuals):
        if hasattr(expected, "search"):
            assert expected.search(actual), f"{actual!r} didn't match {expected!r}"
        else:
            assert expected == actual


@contextlib.contextmanager
def swallow_warnings(
    message: str = r".",
    category: type[Warning] = CoverageWarning,
) -> Iterator[None]:
    """Swallow particular warnings.

    It's OK if they happen, or if they don't happen. Just ignore them.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=category, message=message)
        yield


xfail_pypy38 = pytest.mark.xfail(
    env.PYPY and env.PYVERSION[:2] == (3, 8) and env.PYPYVERSION < (7, 3, 11),
    reason="These tests fail on older PyPy 3.8",
)


class FailingProxy:
    """A proxy for another object, but one method will fail a few times before working."""
    def __init__(self, obj: Any, methname: str, fails: list[Exception]) -> None:
        """Create the failing proxy.

        `obj` is the object to proxy.  `methname` is the method that will fail
        a few times.  `fails` are the exceptions to fail with. Once used up,
        the method will proxy correctly.

        """
        self.obj = obj
        self.methname = methname
        self.fails = fails

    def __getattr__(self, name: str) -> Any:
        if name == self.methname and self.fails:
            meth = self._make_failing_method(self.fails[0])
            del self.fails[0]
        else:
            meth = getattr(self.obj, name)
        return meth

    def _make_failing_method(self, exc: Exception) -> Callable[..., NoReturn]:
        """Return a function that will raise `exc`."""
        def _meth(*args: Any, **kwargs: Any) -> NoReturn:
            raise exc
        return _meth


class DebugControlString(DebugControl):
    """A `DebugControl` that writes to a StringIO, for testing."""
    def __init__(self, options: Iterable[str]) -> None:
        self.io = io.StringIO()
        super().__init__(options, self.io)

    def get_output(self) -> str:
        """Get the output text from the `DebugControl`."""
        return self.io.getvalue()


TestMethod = Callable[[Any], None]

def flaky_method(max_runs: int) -> Callable[[TestMethod], TestMethod]:
    """flaky.flaky, but with type annotations."""
    def _decorator(fn: TestMethod) -> TestMethod:
        return cast(TestMethod, flaky.flaky(max_runs)(fn))
    return _decorator
