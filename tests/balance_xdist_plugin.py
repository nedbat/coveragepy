# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""
A pytest plugin to record test times and then use those times to divide tests
into evenly balanced workloads for each xdist worker.

Two things are hard-coded here that shouldn't be:

- The timing data is written to the tmp directory, but should use the pytest
  cache (https://docs.pytest.org/en/latest/how-to/cache.html).

- The number of xdist workers is hard-coded to 8 because I couldn't figure out
  how to find the number.  Would it be crazy to read the -n argument directly?

You can force some tests to run on the same worker by setting the
`balanced_clumps` setting in your pytest config file.  Each line is a substring
of a test name.  All tests with that substring (like -k) will run on the
worker:

    balanced_clumps =
        LongRunningFixture
        some_other_test_substring

"""

import collections
import csv
import os
import shutil
import time
from pathlib import Path

import pytest
import xdist.scheduler


def pytest_addoption(parser):
    """Auto-called to define ini-file settings."""
    parser.addini(
        "balanced_clumps",
        type="linelist",
        help="Test substrings to assign to the same worker",
    )

@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """Registers our pytest plugin."""
    config.pluginmanager.register(BalanceXdistPlugin(config), "balance_xdist_plugin")


class BalanceXdistPlugin:       # pragma: debugging
    """The plugin"""

    def __init__(self, config):
        self.config = config
        self.running_all = (self.config.getoption("-k") == "")
        self.times = collections.defaultdict(float)
        self.worker = os.environ.get("PYTEST_XDIST_WORKER", "none")
        self.tests_csv = None

    def pytest_sessionstart(self, session):
        """Called once before any tests are run, but in every worker."""
        if not self.running_all:
            return

        tests_csv_dir = Path(session.startdir).resolve() / "tmp/tests_csv"
        self.tests_csv = tests_csv_dir / f"{self.worker}.csv"

        if self.worker == "none":
            if tests_csv_dir.exists():
                for csv_file in tests_csv_dir.iterdir():
                    with csv_file.open(newline="") as fcsv:
                        reader = csv.reader(fcsv)
                        for row in reader:
                            self.times[row[1]] += float(row[3])
                shutil.rmtree(tests_csv_dir)

    def write_duration_row(self, item, phase, duration):
        """Helper to write a row to the tracked-test csv file."""
        if self.running_all:
            self.tests_csv.parent.mkdir(parents=True, exist_ok=True)
            with self.tests_csv.open("a", newline="") as fcsv:
                csv.writer(fcsv).writerow([self.worker, item.nodeid, phase, duration])

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_setup(self, item):
        """Run once for each test."""
        start = time.time()
        yield
        self.write_duration_row(item, "setup", time.time() - start)

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_call(self, item):
        """Run once for each test."""
        start = time.time()
        yield
        self.write_duration_row(item, "call", time.time() - start)

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_teardown(self, item):
        """Run once for each test."""
        start = time.time()
        yield
        self.write_duration_row(item, "teardown", time.time() - start)

    @pytest.hookimpl(trylast=True)
    def pytest_xdist_make_scheduler(self, config, log):
        """Create our BalancedScheduler using time data from the last run."""
        # Assign tests to chunks
        nchunks = 8
        totals = [0] * nchunks
        tests = collections.defaultdict(set)

        # first put the difficult ones all in one worker
        clumped = set()
        clumps = config.getini("balanced_clumps")
        for i, clump_word in enumerate(clumps):
            clump_nodes = set(nodeid for nodeid in self.times.keys() if clump_word in nodeid)
            i %= nchunks
            tests[i].update(clump_nodes)
            totals[i] += sum(self.times[nodeid] for nodeid in clump_nodes)
            clumped.update(clump_nodes)

        # Then assign the rest in descending order
        rest = [(nodeid, t) for (nodeid, t) in self.times.items() if nodeid not in clumped]
        rest.sort(key=lambda item: item[1], reverse=True)
        for nodeid, t in rest:
            lightest = min(enumerate(totals), key=lambda pair: pair[1])[0]
            tests[lightest].add(nodeid)
            totals[lightest] += t

        test_chunks = {}
        for chunk_id, nodeids in tests.items():
            for nodeid in nodeids:
                test_chunks[nodeid] = chunk_id

        return BalancedScheduler(config, log, clumps, test_chunks)


class BalancedScheduler(xdist.scheduler.LoadScopeScheduling):   # pylint: disable=abstract-method # pragma: debugging
    """A balanced-chunk test scheduler for pytest-xdist."""
    def __init__(self, config, log, clumps, test_chunks):
        super().__init__(config, log)
        self.clumps = clumps
        self.test_chunks = test_chunks

    def _split_scope(self, nodeid):
        """Assign a chunk id to a test node."""
        # If we have a chunk assignment for this node, return it.
        scope = self.test_chunks.get(nodeid)
        if scope is not None:
            return scope

        # If this is a node that should be clumped, clump it.
        for i, clump_word in enumerate(self.clumps):
            if clump_word in nodeid:
                return f"clump{i}"

        # Otherwise every node is a separate chunk.
        return nodeid


# Run this with:
#   python -c "from tests.balance_xdist_plugin import show_worker_times as f; f()"
def show_worker_times():                            # pragma: debugging
    """Ad-hoc utility to show data from the last tracked-test run."""
    times = collections.defaultdict(float)
    tests = collections.defaultdict(int)
    tests_csv_dir = Path("tmp/tests_csv")

    for csv_file in tests_csv_dir.iterdir():
        with csv_file.open(newline="") as fcsv:
            reader = csv.reader(fcsv)
            for row in reader:
                worker = row[0]
                duration = float(row[3])
                times[worker] += duration
                if row[2] == "call":
                    tests[worker] += 1

    for worker in sorted(tests.keys()):
        print(f"{worker}: {tests[worker]:3d} {times[worker]:.2f}")

    total = sum(times.values())
    avg = total / len(times)
    print(f"total: {total:.2f}, avg: {avg:.2f}")
    lo = min(times.values())
    hi = max(times.values())
    print(f"lo = {lo:.2f}; hi = {hi:.2f}; gap = {hi - lo:.2f}; long delta = {hi - avg:.2f}")
