"""Tests of coverage/collector.py and other collectors."""

import re

import coverage
from coverage.backward import StringIO

from tests.coveragetest import CoverageTest


class CollectorTest(CoverageTest):
    """Test specific aspects of the collection process."""

    def test_should_trace_cache(self):
        # The tracers should only invoke should_trace once for each file name.

        # Make some files that invoke each other.
        self.make_file("f1.py", """\
            def f1(x, f):
                return f(x)
            """)

        self.make_file("f2.py", """\
            import f1

            def func(x):
                return f1.f1(x, otherfunc)

            def otherfunc(x):
                return x*x

            for i in range(10):
                func(i)
            """)

        debug_out = StringIO()
        cov = coverage.coverage(
            include=["f1.py"], debug=['trace'], debug_file=debug_out
            )

        # Import the python file, executing it.
        self.start_import_stop(cov, "f2")

        # Grab all the filenames mentioned in debug output, there should be no
        # duplicates.
        trace_lines = [
            l for l in debug_out.getvalue().splitlines()
            if l.startswith("Tracing ") or l.startswith("Not tracing ")
        ]
        filenames = [re.search(r"'[^']+'", l).group() for l in trace_lines]
        self.assertEqual(len(filenames), len(set(filenames)))

        # Double-check that the tracing messages are in there somewhere.
        self.assertTrue(len(filenames) > 5)
