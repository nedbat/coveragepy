# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Tests of coverage/debug.py"""

import ast
import io
import os
import re
import sys

import pytest

import coverage
from coverage import env
from coverage.debug import filter_text, info_formatter, info_header, short_id, short_stack
from coverage.debug import clipped_repr

from tests.coveragetest import CoverageTest
from tests.helpers import re_line, re_lines, re_lines_text


class InfoFormatterTest(CoverageTest):
    """Tests of debug.info_formatter."""

    run_in_temp_dir = False

    def test_info_formatter(self):
        lines = list(info_formatter([
            ('x', 'hello there'),
            ('very long label', ['one element']),
            ('regular', ['abc', 'def', 'ghi', 'jkl']),
            ('nothing', []),
        ]))
        expected = [
            '                             x: hello there',
            '               very long label: one element',
            '                       regular: abc',
            '                                def',
            '                                ghi',
            '                                jkl',
            '                       nothing: -none-',
        ]
        assert expected == lines

    def test_info_formatter_with_generator(self):
        lines = list(info_formatter(('info%d' % i, i) for i in range(3)))
        expected = [
            '                         info0: 0',
            '                         info1: 1',
            '                         info2: 2',
        ]
        assert expected == lines

    def test_too_long_label(self):
        with pytest.raises(AssertionError):
            list(info_formatter([('this label is way too long and will not fit', 23)]))


@pytest.mark.parametrize("label, header", [
    ("x",               "-- x ---------------------------------------------------------"),
    ("hello there",     "-- hello there -----------------------------------------------"),
])
def test_info_header(label, header):
    assert info_header(label) == header


@pytest.mark.parametrize("id64, id16", [
    (0x1234, 0x1234),
    (0x12340000, 0x1234),
    (0xA5A55A5A, 0xFFFF),
    (0x1234cba956780fed, 0x8008),
])
def test_short_id(id64, id16):
    assert short_id(id64) == id16


@pytest.mark.parametrize("text, numchars, result", [
    ("hello", 10, "'hello'"),
    ("0123456789abcdefghijklmnopqrstuvwxyz", 15, "'01234...vwxyz'"),
])
def test_clipped_repr(text, numchars, result):
    assert clipped_repr(text, numchars) == result


@pytest.mark.parametrize("text, filters, result", [
    ("hello", [], "hello"),
    ("hello\n", [], "hello\n"),
    ("hello\nhello\n", [], "hello\nhello\n"),
    ("hello\nbye\n", [lambda x: "="+x], "=hello\n=bye\n"),
    ("hello\nbye\n", [lambda x: "="+x, lambda x: x+"\ndone\n"], "=hello\ndone\n=bye\ndone\n"),
])
def test_filter_text(text, filters, result):
    assert filter_text(text, filters) == result


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

        debug_out = io.StringIO()
        cov = coverage.Coverage(debug=debug)
        cov._debug_file = debug_out
        self.start_import_stop(cov, "f1")
        cov.save()

        return debug_out.getvalue()

    def test_debug_no_trace(self):
        out_text = self.f1_debug_output([])

        # We should have no output at all.
        assert not out_text

    def test_debug_trace(self):
        out_text = self.f1_debug_output(["trace"])

        # We should have a line like "Tracing 'f1.py'", perhaps with an
        # absolute path.
        assert re.search(r"Tracing '.*f1.py'", out_text)

        # We should have lines like "Not tracing 'collector.py'..."
        assert re_lines(r"^Not tracing .*: is part of coverage.py$", out_text)

    def test_debug_trace_pid(self):
        out_text = self.f1_debug_output(["trace", "pid"])

        # Now our lines are always prefixed with the process id.
        pid_prefix = r"^%5d\.[0-9a-f]{4}: " % os.getpid()
        pid_lines = re_lines_text(pid_prefix, out_text)
        assert pid_lines == out_text

        # We still have some tracing, and some not tracing.
        assert re_lines(pid_prefix + "Tracing ", out_text)
        assert re_lines(pid_prefix + "Not tracing ", out_text)

    def test_debug_callers(self):
        out_text = self.f1_debug_output(["pid", "dataop", "dataio", "callers", "lock"])
        # For every real message, there should be a stack trace with a line like
        #       "f1_debug_output : /Users/ned/coverage/tests/test_debug.py @71"
        real_messages = re_lines(r":\d+", out_text, match=False)
        frame_pattern = r"\s+f1_debug_output : .*tests[/\\]test_debug.py:\d+$"
        frames = re_lines(frame_pattern, out_text)
        assert len(real_messages) == len(frames)

        last_line = out_text.splitlines()[-1]

        # The details of what to expect on the stack are empirical, and can change
        # as the code changes. This test is here to ensure that the debug code
        # continues working. It's ok to adjust these details over time.
        assert re_lines(r"^\s*\d+\.\w{4}: Adding file tracers: 0 files", real_messages[-1])
        assert re_lines(r"\s+add_file_tracers : .*coverage[/\\]sqldata.py:\d+$", last_line)

    def test_debug_config(self):
        out_text = self.f1_debug_output(["config"])

        labels = """
            attempted_config_files branch config_files_read config_file cover_pylib data_file
            debug exclude_list extra_css html_dir html_title ignore_errors
            run_include run_omit parallel partial_always_list partial_list paths
            precision show_missing source timid xml_output
            report_include report_omit
            """.split()
        for label in labels:
            label_pat = fr"^\s*{label}: "
            msg = f"Incorrect lines for {label!r}"
            assert 1 == len(re_lines(label_pat, out_text)), msg

    def test_debug_sys(self):
        out_text = self.f1_debug_output(["sys"])

        labels = """
            coverage_version coverage_module coverage_paths stdlib_paths third_party_paths
            tracer configs_attempted config_file configs_read data_file
            python platform implementation executable
            pid cwd path environment command_line cover_match pylib_match
            """.split()
        for label in labels:
            label_pat = fr"^\s*{label}: "
            msg = f"Incorrect lines for {label!r}"
            assert 1 == len(re_lines(label_pat, out_text)), msg

    def test_debug_sys_ctracer(self):
        out_text = self.f1_debug_output(["sys"])
        tracer_line = re_line(r"CTracer:", out_text).strip()
        if env.C_TRACER:
            expected = "CTracer: available"
        else:
            expected = "CTracer: unavailable"
        assert expected == tracer_line

    def test_debug_pybehave(self):
        out_text = self.f1_debug_output(["pybehave"])
        out_lines = out_text.splitlines()
        assert 10 < len(out_lines) < 40
        pyversion = re_line(r" PYVERSION:", out_text)
        vtuple = ast.literal_eval(pyversion.partition(":")[-1].strip())
        assert vtuple[:5] == sys.version_info


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
        assert len(stack) > 10
        assert "f_three" in stack[-1]
        assert "f_two" in stack[-2]
        assert "f_one" in stack[-3]

    def test_short_stack_limit(self):
        stack = f_one(limit=5).splitlines()
        assert len(stack) == 5

    def test_short_stack_skip(self):
        stack = f_one(skip=1).splitlines()
        assert "f_two" in stack[-1]
