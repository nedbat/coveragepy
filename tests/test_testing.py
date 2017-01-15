# -*- coding: utf-8 -*-
# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

"""Tests that our test infrastructure is really working!"""

import datetime
import os
import sys

import pytest

import coverage
from coverage.backunittest import TestCase
from coverage.files import actual_path

from tests.coveragetest import CoverageTest
from tests.helpers import CheckUniqueFilenames, re_lines, re_line


class TestingTest(TestCase):
    """Tests of helper methods on `backunittest.TestCase`."""

    def test_assert_count_equal(self):
        self.assertCountEqual(set(), set())
        self.assertCountEqual(set([1,2,3]), set([3,1,2]))
        with self.assertRaises(AssertionError):
            self.assertCountEqual(set([1,2,3]), set())
        with self.assertRaises(AssertionError):
            self.assertCountEqual(set([1,2,3]), set([4,5,6]))


class CoverageTestTest(CoverageTest):
    """Test the methods in `CoverageTest`."""

    def test_arcz_to_arcs(self):
        self.assertEqual(self.arcz_to_arcs(".1 12 2."), [(-1, 1), (1, 2), (2, -1)])
        self.assertEqual(self.arcz_to_arcs("-11 12 2-5"), [(-1, 1), (1, 2), (2, -5)])
        self.assertEqual(
            self.arcz_to_arcs("-QA CB IT Z-A"),
            [(-26, 10), (12, 11), (18, 29), (35, -10)]
        )

    def test_file_exists(self):
        self.make_file("whoville.txt", "We are here!")
        self.assert_exists("whoville.txt")
        self.assert_doesnt_exist("shadow.txt")
        with self.assertRaises(AssertionError):
            self.assert_doesnt_exist("whoville.txt")
        with self.assertRaises(AssertionError):
            self.assert_exists("shadow.txt")

    def test_assert_startwith(self):
        self.assert_starts_with("xyzzy", "xy")
        self.assert_starts_with("xyz\nabc", "xy")
        self.assert_starts_with("xyzzy", ("x", "z"))
        with self.assertRaises(AssertionError):
            self.assert_starts_with("xyz", "a")
        with self.assertRaises(AssertionError):
            self.assert_starts_with("xyz\nabc", "a")

    def test_assert_recent_datetime(self):
        def now_delta(seconds):
            """Make a datetime `seconds` seconds from now."""
            return datetime.datetime.now() + datetime.timedelta(seconds=seconds)

        # Default delta is 10 seconds.
        self.assert_recent_datetime(now_delta(0))
        self.assert_recent_datetime(now_delta(-9))
        with self.assertRaises(AssertionError):
            self.assert_recent_datetime(now_delta(-11))
        with self.assertRaises(AssertionError):
            self.assert_recent_datetime(now_delta(1))

        # Delta is settable.
        self.assert_recent_datetime(now_delta(0), seconds=120)
        self.assert_recent_datetime(now_delta(-100), seconds=120)
        with self.assertRaises(AssertionError):
            self.assert_recent_datetime(now_delta(-1000), seconds=120)
        with self.assertRaises(AssertionError):
            self.assert_recent_datetime(now_delta(1), seconds=120)

    def test_assert_warnings(self):
        cov = coverage.Coverage()

        # Make a warning, it should catch it properly.
        with self.assert_warnings(cov, ["Hello there!"]):
            cov._warn("Hello there!")

        # The expected warnings are regexes.
        with self.assert_warnings(cov, ["Hello.*!"]):
            cov._warn("Hello there!")

        # There can be a bunch of actual warnings.
        with self.assert_warnings(cov, ["Hello.*!"]):
            cov._warn("You there?")
            cov._warn("Hello there!")

        # There can be a bunch of expected warnings.
        with self.assert_warnings(cov, ["Hello.*!", "You"]):
            cov._warn("You there?")
            cov._warn("Hello there!")

        # But if there are a bunch of expected warnings, they have to all happen.
        warn_regex = r"Didn't find warning 'You' in \['Hello there!'\]"
        with self.assertRaisesRegex(AssertionError, warn_regex):
            with self.assert_warnings(cov, ["Hello.*!", "You"]):
                cov._warn("Hello there!")

        # Make a different warning than expected, it should raise an assertion.
        warn_regex = r"Didn't find warning 'Not me' in \['Hello there!'\]"
        with self.assertRaisesRegex(AssertionError, warn_regex):
            with self.assert_warnings(cov, ["Not me"]):
                cov._warn("Hello there!")

        # assert_warnings shouldn't hide a real exception.
        with self.assertRaises(ZeroDivisionError):
            with self.assert_warnings(cov, ["Hello there!"]):
                raise ZeroDivisionError("oops")

    def test_sub_python_is_this_python(self):
        # Try it with a Python command.
        self.set_environ('COV_FOOBAR', 'XYZZY')
        self.make_file("showme.py", """\
            import os, sys
            print(sys.executable)
            print(os.__file__)
            print(os.environ['COV_FOOBAR'])
            """)
        out = self.run_command("python showme.py").splitlines()
        self.assertEqual(actual_path(out[0]), actual_path(sys.executable))
        self.assertEqual(out[1], os.__file__)
        self.assertEqual(out[2], 'XYZZY')

        # Try it with a "coverage debug sys" command.
        out = self.run_command("coverage debug sys")

        executable = re_line(out, "executable:")
        executable = executable.split(":", 1)[1].strip()
        self.assertTrue(_same_python_executable(executable, sys.executable))

        # "environment: COV_FOOBAR = XYZZY" or "COV_FOOBAR = XYZZY"
        environ = re_line(out, "COV_FOOBAR")
        _, _, environ = environ.rpartition(":")
        self.assertEqual(environ.strip(), "COV_FOOBAR = XYZZY")


class CheckUniqueFilenamesTest(CoverageTest):
    """Tests of CheckUniqueFilenames."""

    run_in_temp_dir = False

    class Stub(object):
        """A stand-in for the class we're checking."""
        def __init__(self, x):
            self.x = x

        def method(self, filename, a=17, b="hello"):
            """The method we'll wrap, with args to be sure args work."""
            return (self.x, filename, a, b)

    def test_detect_duplicate(self):
        stub = self.Stub(23)
        CheckUniqueFilenames.hook(stub, "method")

        # Two method calls with different names are fine.
        assert stub.method("file1") == (23, "file1", 17, "hello")
        assert stub.method("file2", 1723, b="what") == (23, "file2", 1723, "what")

        # A duplicate file name trips an assertion.
        with self.assertRaises(AssertionError):
            stub.method("file1")


@pytest.mark.parametrize("text, pat, result", [
    ("line1\nline2\nline3\n", "line", "line1\nline2\nline3\n"),
    ("line1\nline2\nline3\n", "[13]", "line1\nline3\n"),
    ("line1\nline2\nline3\n", "X", ""),
])
def test_re_lines(text, pat, result):
    assert re_lines(text, pat) == result

@pytest.mark.parametrize("text, pat, result", [
    ("line1\nline2\nline3\n", "line", ""),
    ("line1\nline2\nline3\n", "[13]", "line2\n"),
    ("line1\nline2\nline3\n", "X", "line1\nline2\nline3\n"),
])
def test_re_lines_inverted(text, pat, result):
    assert re_lines(text, pat, match=False) == result

@pytest.mark.parametrize("text, pat, result", [
    ("line1\nline2\nline3\n", "2", "line2"),
])
def test_re_line(text, pat, result):
    assert re_line(text, pat) == result

@pytest.mark.parametrize("text, pat", [
    ("line1\nline2\nline3\n", "line"),      # too many matches
    ("line1\nline2\nline3\n", "X"),         # no matches
])
def test_re_line_bad(text, pat):
    with pytest.raises(AssertionError):
        re_line(text, pat)


def _same_python_executable(e1, e2):
    """Determine if `e1` and `e2` refer to the same Python executable.

    Either path could include symbolic links.  The two paths might not refer
    to the exact same file, but if they are in the same directory and their
    numeric suffixes aren't different, they are the same executable.

    """
    e1 = os.path.abspath(os.path.realpath(e1))
    e2 = os.path.abspath(os.path.realpath(e2))

    if os.path.dirname(e1) != os.path.dirname(e2):
        return False                                    # pragma: only failure

    e1 = os.path.basename(e1)
    e2 = os.path.basename(e2)

    if e1 == "python" or e2 == "python" or e1 == e2:
        # Python and Python2.3: OK
        # Python2.3 and Python: OK
        # Python and Python: OK
        # Python2.3 and Python2.3: OK
        return True

    return False                                        # pragma: only failure
