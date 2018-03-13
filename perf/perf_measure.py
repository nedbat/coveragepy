# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

# Run like this:
#   .tox/py36/bin/python perf/perf_measure.py

from collections import namedtuple
import os
import statistics
import sys
import tempfile
import time

from unittest_mixins.mixins import make_file

import coverage
from coverage.backward import import_local_file

from tests.helpers import SuperModuleCleaner


class StressResult(namedtuple('StressResult', ['files', 'calls', 'lines', 'baseline', 'covered'])):
    @property
    def overhead(self):
        return self.covered - self.baseline


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
    lines.extend(
        "import test{}".format(idx) for idx in range(file_count)
    )
    lines.extend(
        "test{}.parent({}, {})".format(idx, call_count, line_count) for idx in range(file_count)
    )
    return "\n".join(lines)


class StressTest(object):

    def __init__(self):
        self.module_cleaner = SuperModuleCleaner()

    def _run_scenario(self, file_count, call_count, line_count):
        self.module_cleaner.clean_local_file_imports()

        for idx in range(file_count):
            make_file('test{}.py'.format(idx), TEST_FILE)
        make_file('testmain.py', mk_main(file_count, call_count, line_count))

        # Run it once just to get the disk caches loaded up.
        import_local_file("testmain")
        self.module_cleaner.clean_local_file_imports()

        # Run it to get the baseline time.
        start = time.perf_counter()
        import_local_file("testmain")
        baseline = time.perf_counter() - start
        self.module_cleaner.clean_local_file_imports()

        # Run it to get the covered time.
        start = time.perf_counter()
        cov = coverage.Coverage()
        cov.start()
        try:                                    # pragma: nested
            # Import the Python file, executing it.
            import_local_file("testmain")
        finally:                                # pragma: nested
            # Stop coverage.py.
            covered = time.perf_counter() - start
            stats = cov._collector.tracers[0].get_stats()
            if stats:
                stats = stats.copy()
            cov.stop()

        return baseline, covered, stats

    def _compute_overhead(self, file_count, call_count, line_count):
        baseline, covered, stats = self._run_scenario(file_count, call_count, line_count)

        #print("baseline = {:.2f}, covered = {:.2f}".format(baseline, covered))
        # Empirically determined to produce the same numbers as the collected
        # stats from get_stats(), with Python 3.6.
        actual_file_count = 17 + file_count
        actual_call_count = file_count * call_count + 156 * file_count + 85
        actual_line_count = (
            2 * file_count * call_count * line_count +
            3 * file_count * call_count +
            769 * file_count +
            345
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

    fixed = 200
    numlo = 100
    numhi = 100
    step = 50
    runs = 5

    def count_operations(self):

        def operations(thing):
            for _ in range(self.runs):
                for n in range(self.numlo, self.numhi+1, self.step):
                    kwargs = {
                        "file_count": self.fixed,
                        "call_count": self.fixed,
                        "line_count": self.fixed,
                    }
                    kwargs[thing+"_count"] = n
                    yield kwargs['file_count'] * kwargs['call_count'] * kwargs['line_count']

        ops = sum(sum(operations(thing)) for thing in ["file", "call", "line"])
        print("{0:.1f}M operations".format(ops/1e6))

    def check_coefficients(self):
        # For checking the calculation of actual stats:
        for f in range(1, 6):
            for c in range(1, 6):
                for l in range(1, 6):
                    _, _, stats = self._run_scenario(f, c, l)
                    print("{0},{1},{2},{3[files]},{3[calls]},{3[lines]}".format(f, c, l, stats))

    def stress_test(self):
        # For checking the overhead for each component:
        def time_thing(thing):
            per_thing = []
            pct_thing = []
            for _ in range(self.runs):
                for n in range(self.numlo, self.numhi+1, self.step):
                    kwargs = {
                        "file_count": self.fixed,
                        "call_count": self.fixed,
                        "line_count": self.fixed,
                    }
                    kwargs[thing+"_count"] = n
                    res = self._compute_overhead(**kwargs)
                    per_thing.append(res.overhead / getattr(res, "{}s".format(thing)))
                    pct_thing.append(res.covered / res.baseline * 100)

            out = "Per {}: ".format(thing)
            out += "mean = {:9.3f}us, stddev = {:8.3f}us, ".format(
                statistics.mean(per_thing)*1e6, statistics.stdev(per_thing)*1e6
            )
            out += "min = {:9.3f}us, ".format(min(per_thing)*1e6)
            out += "pct = {:6.1f}%, stddev = {:6.1f}%".format(
                statistics.mean(pct_thing), statistics.stdev(pct_thing)
            )
            print(out)

        time_thing("file")
        time_thing("call")
        time_thing("line")


if __name__ == '__main__':
    with tempfile.TemporaryDirectory(prefix="coverage_stress_") as tempdir:
        print("Working in {}".format(tempdir))
        os.chdir(tempdir)
        sys.path.insert(0, ".")

        StressTest().stress_test()
