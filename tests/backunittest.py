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
    if _need('assertSameElements'):
        def assertSameElements(self, s1, s2):
            """Assert that the two arguments are equal as sets."""
            self.assertEqual(set(s1), set(s2))
