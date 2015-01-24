"""Tests of coverage/debug.py"""

import os
import re

import coverage
from coverage.backward import StringIO
from coverage.debug import info_formatter
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
        cov = coverage.coverage(debug=debug)
        cov._debug_file = debug_out
        self.start_import_stop(cov, "f1")

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
            version coverage cover_dir pylib_dirs tracer config_files
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


def lines_matching(lines, pat):
    """Gives the list of lines from `lines` that match `pat`."""
    return [l for l in lines if re.search(pat, l)]
