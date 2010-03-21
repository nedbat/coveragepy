"""Tests that our test infrastructure is really working!"""

import os, sys
sys.path.insert(0, os.path.split(__file__)[0]) # Force relative import for Py3k
from backunittest import TestCase
from coveragetest import CoverageTest

from coverage.backward import set                   # pylint: disable-msg=W0622

class TestingTest(TestCase):
    """Tests of helper methods on `backunittest.TestCase`."""

    run_in_temp_dir = False

    def please_raise(self, exc, msg):
        """Raise an exception for testing assertRaisesRegexp."""
        raise exc(msg)

    def please_succeed(self):
        """A simple successful method for testing assertRaisesRegexp."""
        return "All is well"

    def test_assert_same_elements(self):
        self.assertSameElements(set(), set())
        self.assertSameElements(set([1,2,3]), set([3,1,2]))
        self.assertRaises(AssertionError, self.assertSameElements,
            set([1,2,3]), set()
            )
        self.assertRaises(AssertionError, self.assertSameElements,
            set([1,2,3]), set([4,5,6])
            )

    def test_assert_regexp_matches(self):
        self.assertRegexpMatches("hello", "hel*o")
        self.assertRegexpMatches("Oh, hello there!", "hel*o")
        self.assertRaises(AssertionError, self.assertRegexpMatches,
            "hello there", "^hello$"
            )

    def test_assert_multiline_equal(self):
        self.assertMultiLineEqual("hello", "hello")
        self.assertRaises(AssertionError, self.assertMultiLineEqual,
            "hello there", "Hello there"
            )
        self.assertRaises(AssertionError, self.assertMultiLineEqual,
            "hello\nthere", "hello\nThere"
            )

    def test_assert_raises_regexp(self):
        # Raising the right error with the right message passes.
        self.assertRaisesRegexp(
            ZeroDivisionError, "Wow! Zero!",
            self.please_raise, ZeroDivisionError, "Wow! Zero!"
            )
        # Raising the right error with a match passes.
        self.assertRaisesRegexp(
            ZeroDivisionError, "Zero",
            self.please_raise, ZeroDivisionError, "Wow! Zero!"
            )
        # Raising the right error with a mismatch fails.
        self.assertRaises(AssertionError,
            self.assertRaisesRegexp, ZeroDivisionError, "XYZ",
            self.please_raise, ZeroDivisionError, "Wow! Zero!"
            )
        # Raising the right error with a mismatch fails.
        self.assertRaises(AssertionError,
            self.assertRaisesRegexp, ZeroDivisionError, "XYZ",
            self.please_raise, ZeroDivisionError, "Wow! Zero!"
            )
        # Raising the wrong error raises the error itself.
        self.assertRaises(ZeroDivisionError,
            self.assertRaisesRegexp, IOError, "Wow! Zero!",
            self.please_raise, ZeroDivisionError, "Wow! Zero!"
            )
        # Raising no error fails.
        self.assertRaises(AssertionError,
            self.assertRaisesRegexp, ZeroDivisionError, "XYZ",
            self.please_succeed
            )

    def test_assert_true(self):
        self.assertTrue(True)
        self.assertRaises(AssertionError, self.assertTrue, False)

    def test_assert_false(self):
        self.assertFalse(False)
        self.assertRaises(AssertionError, self.assertFalse, True)


class CoverageTestTest(CoverageTest):
    """Test the methods in `CoverageTest`."""

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
        self.make_file("sub/deeper/evenmore/third.txt", "Third")
        self.assertEqual(open("sub/deeper/evenmore/third.txt").read(), "Third")
