# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

"""Tests of coverage/debug.py"""

import os
import re

import coverage
from coverage.backward import StringIO
from coverage.debug import info_formatter, info_header, short_stack

from tests.coveragetest import CoverageTest


class InfoFormatterTest(CoverageTest):
    """Tests of misc.info_formatter."""

    run_in_temp_dir = False

    def test_info_formatter(self):
        lines = list(info_formatter([
            ('x', 'hello there'),
            ('very long label', ['one element']),
            ('regular', ['abc', 'def', 'ghi', 'jkl']),
            ('nothing', []),
        ]))
        self.assertEqual(lines, [
            '              x: hello there',
            'very long label: one element',
            '        regular: abc',
            '                 def',
            '                 ghi',
            '                 jkl',
            '        nothing: -none-',
        ])

    def test_info_formatter_with_generator(self):
        lines = list(info_formatter(('info%d' % i, i) for i in range(3)))
        self.assertEqual(lines, ['info0: 0', 'info1: 1', 'info2: 2'])

    def test_info_header(self):
        self.assertEqual(
            info_header("x"),
            "-- x ---------------------------------------------------------"
        )
        self.assertEqual(
            info_header("hello there"),
            "-- hello there -----------------------------------------------"
        )


class DebugTraceTest(CoverageTest):
    """Tests of debug output."""

    def f1_debug_output(self, debug):
        """Runs some code with `debug` option, returns the debug output."""
        # Make code to run.
        self.make_file("f1.py", """\
            def f1(x):
                return x+1

            for i in range(5):
                f1(i)
            """)

        debug_out = StringIO()
        cov = coverage.Coverage(debug=debug)
        cov._debug_file = debug_out
        self.start_import_stop(cov, "f1")
        cov.save()

        out_lines = debug_out.getvalue().splitlines()
        return out_lines

    def test_debug_no_trace(self):
        out_lines = self.f1_debug_output([])

        # We should have no output at all.
        self.assertFalse(out_lines)

    def test_debug_trace(self):
        out_lines = self.f1_debug_output(["trace"])

        # We should have a line like "Tracing 'f1.py'"
        self.assertIn("Tracing 'f1.py'", out_lines)

        # We should have lines like "Not tracing 'collector.py'..."
        coverage_lines = lines_matching(
            out_lines,
            r"^Not tracing .*: is part of coverage.py$"
            )
        self.assertTrue(coverage_lines)

    def test_debug_trace_pid(self):
        out_lines = self.f1_debug_output(["trace", "pid"])

        # Now our lines are always prefixed with the process id.
        pid_prefix = "^pid %5d: " % os.getpid()
        pid_lines = lines_matching(out_lines, pid_prefix)
        self.assertEqual(pid_lines, out_lines)

        # We still have some tracing, and some not tracing.
        self.assertTrue(lines_matching(out_lines, pid_prefix + "Tracing "))
        self.assertTrue(lines_matching(out_lines, pid_prefix + "Not tracing "))

    def test_debug_callers(self):
        out_lines = self.f1_debug_output(["pid", "dataop", "dataio", "callers"])
        print("\n".join(out_lines))
        # For every real message, there should be a stack
        # trace with a line like "f1_debug_output : /Users/ned/coverage/tests/test_debug.py @71"
        real_messages = lines_matching(out_lines, r"^pid\s+\d+: ")
        frame_pattern = r"\s+f1_debug_output : .*tests[/\\]test_debug.py @\d+$"
        frames = lines_matching(out_lines, frame_pattern)
        self.assertEqual(len(real_messages), len(frames))

        # The last message should be "Writing data", and the last frame should
        # be write_file in data.py.
        self.assertRegex(real_messages[-1], r"^pid\s+\d+: Writing data")
        self.assertRegex(out_lines[-1], r"\s+write_file : .*coverage[/\\]data.py @\d+$")

    def test_debug_config(self):
        out_lines = self.f1_debug_output(["config"])

        labels = """
            attempted_config_files branch config_files cover_pylib data_file
            debug exclude_list extra_css html_dir html_title ignore_errors
            include omit parallel partial_always_list partial_list paths
            precision show_missing source timid xml_output
            """.split()
        for label in labels:
            label_pat = r"^\s*%s: " % label
            self.assertEqual(len(lines_matching(out_lines, label_pat)), 1)

    def test_debug_sys(self):
        out_lines = self.f1_debug_output(["sys"])

        labels = """
            version coverage cover_dirs pylib_dirs tracer config_files
            configs_read data_path python platform implementation executable
            cwd path environment command_line cover_match pylib_match
            """.split()
        for label in labels:
            label_pat = r"^\s*%s: " % label
            self.assertEqual(
                len(lines_matching(out_lines, label_pat)),
                1,
                msg="Incorrect lines for %r" % label,
            )


def f_one(*args, **kwargs):
    """First of the chain of functions for testing `short_stack`."""
    return f_two(*args, **kwargs)

def f_two(*args, **kwargs):
    """Second of the chain of functions for testing `short_stack`."""
    return f_three(*args, **kwargs)

def f_three(*args, **kwargs):
    """Third of the chain of functions for testing `short_stack`."""
    return short_stack(*args, **kwargs)


class ShortStackTest(CoverageTest):
    """Tests of coverage.debug.short_stack."""

    run_in_temp_dir = False

    def test_short_stack(self):
        stack = f_one().splitlines()
        self.assertGreater(len(stack), 10)
        self.assertIn("f_three", stack[-1])
        self.assertIn("f_two", stack[-2])
        self.assertIn("f_one", stack[-3])

    def test_short_stack_limit(self):
        stack = f_one(limit=5).splitlines()
        self.assertEqual(len(stack), 5)

    def test_short_stack_skip(self):
        stack = f_one(skip=1).splitlines()
        self.assertIn("f_two", stack[-1])


def lines_matching(lines, pat):
    """Gives the list of lines from `lines` that match `pat`."""
    return [l for l in lines if re.search(pat, l)]
