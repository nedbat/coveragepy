# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""
Pytest auto configuration.

This module is run automatically by pytest, to define and enable fixtures.
"""

import itertools
import os
import sys
import sysconfig
import warnings
from pathlib import Path

import pytest

from coverage import env
from coverage.exceptions import _StopEverything
from coverage.files import set_relative_directory


# Pytest will rewrite assertions in test modules, but not elsewhere.
# This tells pytest to also rewrite assertions in coveragetest.py.
pytest.register_assert_rewrite("tests.coveragetest")
pytest.register_assert_rewrite("tests.helpers")

# Pytest can take additional options:
# $set_env.py: PYTEST_ADDOPTS - Extra arguments to pytest.

@pytest.fixture(autouse=True)
def set_warnings():
    """Configure warnings to show while running tests."""
    warnings.simplefilter("default")
    warnings.simplefilter("once", DeprecationWarning)

    # Warnings to suppress:
    # How come these warnings are successfully suppressed here, but not in setup.cfg??

    # <frozen importlib._bootstrap>:681:
    # ImportWarning: VendorImporter.exec_module() not found; falling back to load_module()
    warnings.filterwarnings(
        "ignore",
        category=ImportWarning,
        message=r".*exec_module\(\) not found; falling back to load_module\(\)",
        )
    # <frozen importlib._bootstrap>:908:
    # ImportWarning: AssertionRewritingHook.find_spec() not found; falling back to find_module()
    # <frozen importlib._bootstrap>:908:
    # ImportWarning: _SixMetaPathImporter.find_spec() not found; falling back to find_module()
    # <frozen importlib._bootstrap>:908:
    # ImportWarning: VendorImporter.find_spec() not found; falling back to find_module()
    warnings.filterwarnings(
        "ignore",
        category=ImportWarning,
        message=r".*find_spec\(\) not found; falling back to find_module\(\)",
        )
    warnings.filterwarnings(
        "ignore",
        category=DeprecationWarning,
        message=r".*imp module is deprecated in favour of importlib",
        )

    if env.PYPY:
        # pypy3 warns about unclosed files a lot.
        warnings.filterwarnings("ignore", r".*unclosed file", category=ResourceWarning)


@pytest.fixture(autouse=True)
def reset_sys_path():
    """Clean up sys.path changes around every test."""
    sys_path = list(sys.path)
    yield
    sys.path[:] = sys_path


@pytest.fixture(autouse=True)
def reset_environment():
    """Make sure a test setting an envvar doesn't leak into another test."""
    old_environ = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(old_environ)


@pytest.fixture(autouse=True)
def reset_filesdotpy_globals():
    """coverage/files.py has some unfortunate globals. Reset them every test."""
    set_relative_directory()
    yield

WORKER = os.environ.get("PYTEST_XDIST_WORKER", "none")

TRACK_TESTS = False
TEST_TXT = "/tmp/tests.txt"

def pytest_sessionstart():
    """Run once at the start of the test session."""
    if TRACK_TESTS:     # pragma: debugging
        with open(TEST_TXT, "w") as testtxt:
            print("Starting:", file=testtxt)

    # Create a .pth file for measuring subprocess coverage.
    if WORKER == "none":
        pth_dir = find_writable_pth_directory()
        assert pth_dir
        (pth_dir / "subcover.pth").write_text("import coverage; coverage.process_startup()\n")
        # subcover.pth is deleted by pytest_sessionfinish below.


def pytest_sessionfinish():
    """Hook the end of a test session, to clean up."""
    # This is called by each of the workers and by the main process.
    if WORKER == "none":
        for pth_dir in possible_pth_dirs():             # pragma: part covered
            pth_file = pth_dir / "subcover.pth"
            if pth_file.exists():
                pth_file.unlink()


def write_test_name(prefix):
    """For tracking where and when tests are running."""
    if TRACK_TESTS:     # pragma: debugging
        with open(TEST_TXT, "a") as testtxt:
            test = os.environ.get("PYTEST_CURRENT_TEST", "unknown")
            print(f"{prefix} {WORKER}: {test}", file=testtxt, flush=True)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    """Run once for each test."""
    write_test_name(">")

    # Convert _StopEverything into skipped tests.
    outcome = yield
    if outcome.excinfo and issubclass(outcome.excinfo[0], _StopEverything):  # pragma: only jython
        pytest.skip(f"Skipping {item.nodeid} for _StopEverything: {outcome.excinfo[1]}")

    write_test_name("<")


def interleaved(firsts, rest, n):
    """Interleave the firsts among the rest so that they occur each n items."""
    num = sum(len(l) for l in firsts) + len(rest)
    lists = firsts + [rest] * (n - len(firsts))
    listcycle = itertools.cycle(lists)

    while num:
        alist = next(listcycle)     # pylint: disable=stop-iteration-return
        if alist:
            yield alist.pop()
            num -= 1


def pytest_collection_modifyitems(items):
    """Re-order the collected tests."""
    # Trick the xdist scheduler to put all of the VirtualenvTest tests on the
    # same worker by sprinkling them into the collected items every Nth place.
    virt = set(i for i in items if "VirtualenvTest" in i.nodeid)
    rest = [i for i in items if i not in virt]
    nworkers = int(os.environ.get("PYTEST_XDIST_WORKER_COUNT", 4))
    items[:] = interleaved([virt], rest, nworkers)
    if TRACK_TESTS:     # pragma: debugging
        with open("/tmp/items.txt", "w") as f:
            print("\n".join(i.nodeid for i in items), file=f)


def possible_pth_dirs():
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


def find_writable_pth_directory():
    """Find a place to write a .pth file."""
    for pth_dir in possible_pth_dirs():             # pragma: part covered
        try_it = pth_dir / f"touch_{WORKER}.it"
        try:
            try_it.write_text("foo")
        except OSError:                             # pragma: cant happen
            continue

        os.remove(try_it)
        return pth_dir

    return None                                     # pragma: cant happen
