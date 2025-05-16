# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""
Pytest auto configuration.

This module is run automatically by pytest, to define and enable fixtures.
"""

from __future__ import annotations

import os
import sys
import sysconfig
import warnings

from pathlib import Path
from collections.abc import Iterator

import pytest

from coverage.files import set_relative_directory

# Pytest will rewrite assertions in test modules, but not elsewhere.
# This tells pytest to also rewrite assertions in these files:
pytest.register_assert_rewrite("tests.coveragetest")
pytest.register_assert_rewrite("tests.helpers")

# Pytest can take additional options:
# $set_env.py: PYTEST_ADDOPTS - Extra arguments to pytest.

pytest_plugins = [
    "tests.balance_xdist_plugin",
    "tests.select_plugin",
]


@pytest.fixture(autouse=True)
def set_warnings() -> None:
    """Configure warnings to show while running tests."""
    warnings.simplefilter("default")
    warnings.simplefilter("once", DeprecationWarning)

    # Warnings to suppress:
    # How come these warnings are successfully suppressed here, but not in pyproject.toml??

    # Note: when writing the regex for the message, it's matched with re.match,
    # so it has to match the beginning of the message.  Add ".*" to make it
    # match something in the middle of the message.

    # Don't warn about unclosed SQLite connections.
    # We don't close ":memory:" databases because we don't have a way to connect
    # to them more than once if we close them.  In real coverage.py uses, there
    # are only a couple of them, but our test suite makes many and we get warned
    # about them all.
    # Python3.13 added this warning, but the behavior has been the same all along,
    # without any reported problems, so just quiet the warning.
    # https://github.com/python/cpython/issues/105539
    warnings.filterwarnings("ignore", r"unclosed database", category=ResourceWarning)

    warnings.filterwarnings("ignore", r".*no-sysmon")

    # We have a test that has a return in a finally: test_bug_1891.
    warnings.filterwarnings("ignore", "'return' in a 'finally' block", category=SyntaxWarning)


@pytest.fixture(autouse=True)
def reset_sys_path() -> Iterator[None]:
    """Clean up sys.path changes around every test."""
    sys_path = list(sys.path)
    yield
    sys.path[:] = sys_path


@pytest.fixture(autouse=True)
def reset_environment() -> Iterator[None]:
    """Make sure a test setting an envvar doesn't leak into another test."""
    old_environ = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(old_environ)


@pytest.fixture(autouse=True)
def reset_filesdotpy_globals() -> None:
    """coverage/files.py has some unfortunate globals. Reset them every test."""
    set_relative_directory()

@pytest.fixture(autouse=True)
def force_local_pyc_files() -> None:
    """Ensure that .pyc files are written next to source files."""
    # For some tests, we need .pyc files written in the current directory,
    # so override any local setting.
    sys.pycache_prefix = None


WORKER = os.getenv("PYTEST_XDIST_WORKER", "none")

def pytest_sessionstart() -> None:
    """Run once at the start of the test session."""
    warnings.filterwarnings("ignore", r".*no-sysmon")
    # Only in the main process...
    if WORKER == "none":
        # Create a .pth file for measuring subprocess coverage.
        pth_dir = find_writable_pth_directory()
        assert pth_dir
        sub_dir = pth_dir / "subcover.pth"
        sub_dir.write_text("import coverage; coverage.process_startup()\n", encoding="utf-8")
        # subcover.pth is deleted by pytest_sessionfinish below.


def pytest_sessionfinish() -> None:
    """Hook the end of a test session, to clean up."""
    # This is called by each of the workers and by the main process.
    if WORKER == "none":
        for pth_dir in possible_pth_dirs():             # pragma: part covered
            pth_file = pth_dir / "subcover.pth"
            if pth_file.exists():
                pth_file.unlink()


def possible_pth_dirs() -> Iterator[Path]:
    """Produce a sequence of directories for trying to write .pth files."""
    # First look through sys.path, and if we find a .pth file, then it's a good
    # place to put ours.
    for pth_dir in map(Path, sys.path):             # pragma: part covered
        pth_files = list(pth_dir.glob("*.pth"))
        if pth_files:
            yield pth_dir

    # If we're still looking, then try the Python library directory.
    # https://github.com/nedbat/coveragepy/issues/339
    yield Path(sysconfig.get_path("purelib"))       # pragma: cant happen


def find_writable_pth_directory() -> Path | None:
    """Find a place to write a .pth file."""
    for pth_dir in possible_pth_dirs():             # pragma: part covered
        try_it = pth_dir / f"touch_{WORKER}.it"
        try:
            try_it.write_text("foo", encoding="utf-8")
        except OSError:                             # pragma: cant happen
            continue

        os.remove(try_it)
        return pth_dir

    return None                                     # pragma: cant happen
