# -*- coding: utf-8 -*-
# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

"""Tests that our test infrastructure is really working!"""

import datetime
import os
import re
import sys
import textwrap

import coverage
from coverage.backunittest import TestCase
from coverage.backward import to_bytes
from coverage.files import actual_path
from coverage.test_helpers import EnvironmentAwareMixin, TempDirMixin, DelayedAssertionMixin

from tests.coveragetest import CoverageTest


class TestingTest(TestCase):
    """Tests of helper methods on `backunittest.TestCase`."""

    def test_assert_count_equal(self):
        self.assertCountEqual(set(), set())
        self.assertCountEqual(set([1,2,3]), set([3,1,2]))
        with self.assertRaises(AssertionError):
            self.assertCountEqual(set([1,2,3]), set())
        with self.assertRaises(AssertionError):
            self.assertCountEqual(set([1,2,3]), set([4,5,6]))


class TempDirMixinTest(TempDirMixin, TestCase):
    """Test the methods in TempDirMixin."""

    def file_text(self, fname):
        """Return the text read from a file."""
        with open(fname, "rb") as f:
            return f.read().decode('ascii')

    def test_make_file(self):
        # A simple file.
        self.make_file("fooey.boo", "Hello there")
        self.assertEqual(self.file_text("fooey.boo"), "Hello there")
        # A file in a sub-directory
        self.make_file("sub/another.txt", "Another")
        self.assertEqual(self.file_text("sub/another.txt"), "Another")
        # A second file in that sub-directory
        self.make_file("sub/second.txt", "Second")
        self.assertEqual(self.file_text("sub/second.txt"), "Second")
        # A deeper directory
        self.make_file("sub/deeper/evenmore/third.txt")
        self.assertEqual(self.file_text("sub/deeper/evenmore/third.txt"), "")

    def test_make_file_newline(self):
        self.make_file("unix.txt", "Hello\n")
        self.assertEqual(self.file_text("unix.txt"), "Hello\n")
        self.make_file("dos.txt", "Hello\n", newline="\r\n")
        self.assertEqual(self.file_text("dos.txt"), "Hello\r\n")
        self.make_file("mac.txt", "Hello\n", newline="\r")
        self.assertEqual(self.file_text("mac.txt"), "Hello\r")

    def test_make_file_non_ascii(self):
        self.make_file("unicode.txt", "tabblo: «ταБЬℓσ»")
        with open("unicode.txt", "rb") as f:
            text = f.read()
        self.assertEqual(text, to_bytes("tabblo: «ταБЬℓσ»"))


class EnvironmentAwareMixinTest(EnvironmentAwareMixin, TestCase):
    """Tests of test_helpers.EnvironmentAwareMixin."""

    def test_setting_and_cleaning_env_vars(self):
        # The before state.
        # Not sure what environment variables are available in all of our
        # different testing environments, so try a bunch.
        for envvar in ["HOME", "HOMEDIR", "USER", "SYSTEMDRIVE", "TEMP"]:   # pragma: part covered
            if envvar in os.environ:
                original_text = os.environ[envvar]
                new_text = "Some Strange Text"
                break
        # pylint: disable=undefined-loop-variable
        self.assertNotEqual(original_text, new_text)
        self.assertNotIn("XYZZY_PLUGH", os.environ)

        # Change the environment.
        self.set_environ(envvar, new_text)
        self.set_environ("XYZZY_PLUGH", "Vogon")

        self.assertEqual(os.environ[envvar], new_text)
        self.assertEqual(os.environ["XYZZY_PLUGH"], "Vogon")

        # Do the clean ups early.
        self.doCleanups()

        # The environment should be restored.
        self.assertEqual(os.environ[envvar], original_text)
        self.assertNotIn("XYZZY_PLUGH", os.environ)


class DelayedAssertionMixinTest(DelayedAssertionMixin, TestCase):
    """Test the `delayed_assertions` method."""

    def test_delayed_assertions(self):
        # Two assertions can be shown at once:
        msg = re.escape(textwrap.dedent("""\
            2 failed assertions:
            'x' != 'y'
            - x
            + y

            'w' != 'z'
            - w
            + z
            """))
        with self.assertRaisesRegex(AssertionError, msg):
            with self.delayed_assertions():
                self.assertEqual("x", "y")
                self.assertEqual("w", "z")

        # It's also OK if only one fails:
        msg = re.escape(textwrap.dedent("""\
            'w' != 'z'
            - w
            + z
            """))
        with self.assertRaisesRegex(AssertionError, msg):
            with self.delayed_assertions():
                self.assertEqual("x", "x")
                self.assertEqual("w", "z")

        # If an error happens, it gets reported immediately, no special
        # handling:
        with self.assertRaises(ZeroDivisionError):
            with self.delayed_assertions():
                self.assertEqual("x", "y")
                self.assertEqual("w", 1/0)


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
        os.environ['COV_FOOBAR'] = 'XYZZY'
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
        out = self.run_command("coverage debug sys").splitlines()
        # "environment: COV_FOOBAR = XYZZY" or "COV_FOOBAR = XYZZY"
        executable = next(l for l in out if "executable:" in l)     # pragma: part covered
        executable = executable.split(":", 1)[1].strip()
        self.assertTrue(same_python_executable(executable, sys.executable))
        environ = next(l for l in out if "COV_FOOBAR" in l)         # pragma: part covered
        _, _, environ = environ.rpartition(":")
        self.assertEqual(environ.strip(), "COV_FOOBAR = XYZZY")


def same_python_executable(e1, e2):
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
