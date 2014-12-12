# -*- coding: utf-8 -*-
"""Tests that our test infrastructure is really working!"""

import os, sys
from coverage.backunittest import TestCase
from coverage.backward import to_bytes
from tests.coveragetest import TempDirMixin, CoverageTest


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


class CoverageTestTest(CoverageTest):
    """Test the methods in `CoverageTest`."""

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
        self.assertEqual(out[0], sys.executable)
        self.assertEqual(out[1], os.__file__)
        self.assertEqual(out[2], 'XYZZY')

        # Try it with a "coverage debug sys" command.
        out = self.run_command("coverage debug sys").splitlines()
        # "environment: COV_FOOBAR = XYZZY" or "COV_FOOBAR = XYZZY"
        executable = next(l for l in out if "executable:" in l)
        executable = executable.split(":", 1)[1].strip()
        self.assertTrue(same_python_executable(executable, sys.executable))
        environ = next(l for l in out if "COV_FOOBAR" in l)
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
