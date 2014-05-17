"""Implementations of unittest features from the future."""

# Use unittest2 if it's available, otherwise unittest.  This gives us
# backported features for 2.6.
try:
    import unittest2 as unittest            # pylint: disable=F0401
except ImportError:
    import unittest


def _need(method):
    """Do we need to define our own `method` method?"""
    return not hasattr(unittest.TestCase, method)


class TestCase(unittest.TestCase):
    """Just like unittest.TestCase, but with assert methods added.

    Designed to be compatible with 3.1 unittest.  Methods are only defined if
    `unittest` doesn't have them.

    """
    if _need('assertCountEqual'):
        try:
            assertCountEqual = assertSameElements
        except NameError:
            def assertCountEqual(self, s1, s2):
                """Assert these have the same elements, regardless of order."""
                self.assertEqual(set(s1), set(s2))
        else:
            def assertCountEqual(self, *args, **kwargs):
                return self.assertSameElements(*args, **kwargs)

    if _need('assertRaisesRegex'):
        def assertRaisesRegex(self, *args, **kwargs):
            return self.assertRaisesRegexp(*args, **kwargs)

    if _need('assertRegex'):
        def assertRegex(self, *args, **kwargs):
            return self.assertRegexpMatches(*args, **kwargs)
