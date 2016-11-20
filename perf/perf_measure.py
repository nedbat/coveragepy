# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

import csv
from collections import namedtuple
import os
import shutil
import statistics
import sys
import time

import coverage
from tests.coveragetest import CoverageTest


class StressResult(namedtuple('StressResult', ['files', 'calls', 'lines', 'baseline', 'covered'])):
    @property
    def overhead(self):
        return self.covered - self.baseline


NANOS = 1e9

TEST_FILE = """\
def parent(call_count, line_count):
    for _ in range(call_count):
        child(line_count)

def child(line_count):
    for i in range(line_count):
        x = 1
"""

def mk_main(file_count, call_count, line_count):
    lines = []
    lines.extend("import test{}".format(idx) for idx in range(file_count))
    lines.extend("test{}.parent({}, {})".format(idx, call_count, line_count) for idx in range(file_count))

    return "\n".join(lines)


class StressTest(CoverageTest):

    def _compute_overhead(self, file_count, call_count, line_count):
        self.clean_local_file_imports()

        for idx in range(file_count):
            self.make_file('test{}.py'.format(idx), TEST_FILE)
        self.make_file('testmain.py', mk_main(file_count, call_count, line_count))

        # Run it once just to get the disk caches loaded up.
        self.import_local_file("testmain")
        self.clean_local_file_imports()

        # Run it to get the baseline time.
        start = time.perf_counter()
        self.import_local_file("testmain")
        baseline = time.perf_counter() - start
        self.clean_local_file_imports()

        # Run it to get the covered time.
        start = time.perf_counter()
        cov = coverage.Coverage()
        cov.start()
        try:                                    # pragma: nested
            # Import the Python file, executing it.
            mod = self.import_local_file("testmain")
        finally:                                # pragma: nested
            # Stop coverage.py.
            covered = time.perf_counter() - start
            stats = cov.collector.tracers[0].get_stats()
            if stats:
                stats = stats.copy()
            cov.stop()

        print("baseline = {:.2f}, covered = {:.2f}".format(baseline, covered))
        # Empirically determined to produce the same numbers as the collected
        # stats from get_stats().
        actual_file_count = 6 + file_count
        actual_call_count = 85 + file_count * (call_count + 98)
        actual_line_count = (
            343 +
            390 * file_count +
            3 * file_count * call_count +
            2 * file_count * call_count * line_count
        )

        if stats is not None:
            assert actual_file_count == stats['files']
            assert actual_call_count == stats['calls']
            assert actual_line_count == stats['lines']
            print("File counts", file_count, actual_file_count, stats['files'])
            print("Call counts", call_count, actual_call_count, stats['calls'])
            print("Line counts", line_count, actual_line_count, stats['lines'])
            print()

        return StressResult(
            actual_file_count,
            actual_call_count,
            actual_line_count,
            baseline,
            covered,
        )

    def stress_test(self):

        # For checking the calculation of actual stats:
        if 0:
            for f in range(3):
                for c in range(3):
                    for l in range(3):
                        self._compute_overhead(100*f+1, 100*c+1, 100*l+1)

        # For checking the overhead for each component:
        fixed = 900
        step = 500

        def time_thing(thing):
            per_thing = []
            pct_thing = []
            for runs in range(5):
                for n in range(100, 1000, step):
                    kwargs = {
                        "file_count": fixed,
                        "call_count": fixed,
                        "line_count": fixed,
                    }
                    kwargs[thing+"_count"] = n
                    res = self._compute_overhead(**kwargs)
                    per_thing.append(res.overhead / getattr(res, "{}s".format(thing)))
                    pct_thing.append(res.covered / res.baseline * 100)

            print("Per {}: mean = {:.5f}us, stddev = {:0.5f}us".format(thing, statistics.mean(per_thing)*1e6, statistics.stdev(per_thing)*1e6))
            print("          pct = {:.3f}%, stddev = {:.5f}".format(statistics.mean(pct_thing), statistics.stdev(pct_thing)))

        time_thing("file")
        time_thing("call")
        time_thing("line")

        return

        line_result = self._compute_overhead(1, 1, int(1e8))
        call_result = self._compute_overhead(1, int(1e7), 1)
        file_result = self._compute_overhead(int(1e4), 1, 1)

        line_overhead_estimate = 0
        call_overhead_estimate = 0
        file_overhead_estimate = 0

        for i in range(20):
            line_overhead_estimate = (
                line_result.overhead * NANOS -
                call_overhead_estimate * line_result.calls -
                file_overhead_estimate * line_result.files
            ) / line_result.lines

            call_overhead_estimate = (
                call_result.overhead * NANOS -
                line_overhead_estimate * call_result.lines -
                file_overhead_estimate * call_result.files
            ) / call_result.calls

            file_overhead_estimate = (
                file_result.overhead * NANOS -
                call_overhead_estimate * file_result.calls -
                line_overhead_estimate * file_result.lines
            ) / file_result.files

        line_baseline_estimate = 0
        call_baseline_estimate = 0
        file_baseline_estimate = 0

        for i in range(20):
            line_baseline_estimate = (
                line_result.baseline * NANOS -
                call_baseline_estimate * line_result.calls -
                file_baseline_estimate * line_result.files
            ) / line_result.lines

            call_baseline_estimate = (
                call_result.baseline * NANOS -
                line_baseline_estimate * call_result.lines -
                file_baseline_estimate * call_result.files
            ) / call_result.calls

            file_baseline_estimate = (
                file_result.baseline * NANOS -
                call_baseline_estimate * file_result.calls -
                line_baseline_estimate * file_result.lines
            ) / file_result.files

        print("Line: {:.2f} ns baseline, {:.2f} ns overhead, {:.2%} overhead".format(
            line_baseline_estimate,
            line_overhead_estimate,
            line_overhead_estimate/line_baseline_estimate,
        ))

        print("Call: {:.2f} ns baseline, {:.2f} ns overhead, {:.2%} overhead".format(
            call_baseline_estimate,
            call_overhead_estimate,
            call_overhead_estimate/call_baseline_estimate,
        ))

        print("File: {:.2f} ns baseline, {:.2f} ns overhead, {:.2%} overhead".format(
            file_baseline_estimate,
            file_overhead_estimate,
            file_overhead_estimate/file_baseline_estimate,
        ))

        assert False
