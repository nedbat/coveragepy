# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""
Pytest auto configuration.

This module is run automatically by pytest, to define and enable fixtures.
"""

import itertools
import os
import sys
import warnings

import pytest

from coverage import env
from coverage.exceptions import StopEverything


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


TRACK_TESTS = False
TEST_TXT = "/tmp/tests.txt"

def pytest_sessionstart():
    """Run once at the start of the test session."""
    if TRACK_TESTS:     # pragma: debugging
        with open(TEST_TXT, "w") as testtxt:
            print("Starting:", file=testtxt)


def write_test_name(prefix):
    """For tracking where and when tests are running."""
    if TRACK_TESTS:     # pragma: debugging
        with open(TEST_TXT, "a") as testtxt:
            worker = os.environ.get('PYTEST_XDIST_WORKER', 'none')
            test = os.environ.get("PYTEST_CURRENT_TEST", "unknown")
            print(f"{prefix} {worker}: {test}", file=testtxt, flush=True)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    """Run once for each test."""
    write_test_name(">")

    # Convert StopEverything into skipped tests.
    outcome = yield
    if outcome.excinfo and issubclass(outcome.excinfo[0], StopEverything):  # pragma: only jython
        pytest.skip(f"Skipping {item.nodeid} for StopEverything: {outcome.excinfo[1]}")

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
