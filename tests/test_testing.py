# -*- coding: utf-8 -*-
"""Tests that our test infrastructure is really working!"""

import os, sys
from coverage.backward import to_bytes
from tests.backunittest import TestCase
from tests.coveragetest import CoverageTest


class TestingTest(TestCase):
    """Tests of helper methods on `backunittest.TestCase`."""

    run_in_temp_dir = False

    def test_assert_same_elements(self):
        self.assertSameElements(set(), set())
        self.assertSameElements(set([1,2,3]), set([3,1,2]))
        self.assertRaises(AssertionError, self.assertSameElements,
            set([1,2,3]), set()
            )
        self.assertRaises(AssertionError, self.assertSameElements,
            set([1,2,3]), set([4,5,6])
            )


class CoverageTestTest(CoverageTest):
    """Test the methods in `CoverageTest`."""

    def file_text(self, fname):
        """Return the text read from a file."""
        return open(fname, "rb").read().decode('ascii')

    def test_make_file(self):
        # A simple file.
        self.make_file("fooey.boo", "Hello there")
        self.assertEqual(open("fooey.boo").read(), "Hello there")
        # A file in a sub-directory
        self.make_file("sub/another.txt", "Another")
        self.assertEqual(open("sub/another.txt").read(), "Another")
        # A second file in that sub-directory
        self.make_file("sub/second.txt", "Second")
        self.assertEqual(open("sub/second.txt").read(), "Second")
        # A deeper directory
        self.make_file("sub/deeper/evenmore/third.txt")
        self.assertEqual(open("sub/deeper/evenmore/third.txt").read(), "")

    def test_make_file_newline(self):
        self.make_file("unix.txt", "Hello\n")
        self.assertEqual(self.file_text("unix.txt"), "Hello\n")
        self.make_file("dos.txt", "Hello\n", newline="\r\n")
        self.assertEqual(self.file_text("dos.txt"), "Hello\r\n")
        self.make_file("mac.txt", "Hello\n", newline="\r")
        self.assertEqual(self.file_text("mac.txt"), "Hello\r")

    def test_make_file_non_ascii(self):
        self.make_file("unicode.txt", "tabblo: «ταБЬℓσ»")
        self.assertEqual(
            open("unicode.txt", "rb").read(),
            to_bytes("tabblo: «ταБЬℓσ»")
            )

    def test_file_exists(self):
        self.make_file("whoville.txt", "We are here!")
        self.assert_exists("whoville.txt")
        self.assert_doesnt_exist("shadow.txt")
        self.assertRaises(
            AssertionError, self.assert_doesnt_exist, "whoville.txt"
            )
        self.assertRaises(AssertionError, self.assert_exists, "shadow.txt")

    def test_assert_startwith(self):
        self.assert_starts_with("xyzzy", "xy")
        self.assert_starts_with("xyz\nabc", "xy")
        self.assert_starts_with("xyzzy", ("x", "z"))
        self.assertRaises(
            AssertionError, self.assert_starts_with, "xyz", "a"
        )
        self.assertRaises(
            AssertionError, self.assert_starts_with, "xyz\nabc", "a"
        )

    def test_sub_python_is_this_python(self):
        # Try it with a python command.
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
        return False

    e1 = os.path.basename(e1)
    e2 = os.path.basename(e2)

    if e1 == "python" or e2 == "python" or e1 == e2:
        # python and python2.3: ok
        # python2.3 and python: ok
        # python and python: ok
        # python2.3 and python2.3: ok
        return True

    return False
