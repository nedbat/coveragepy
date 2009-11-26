"""Implementations of unittest features from the future."""

import difflib, re, sys, unittest

from coverage.backward import set                   # pylint: disable-msg=W0622

class TestCase(unittest.TestCase):
    """Just like unittest.TestCase, but with assert methods added.
    
    Designed to be compatible with 3.1 unittest.
    
    """
    def assert_raises_msg(self, excClass, msg, callableObj, *args, **kwargs):
        """ Just like unittest.TestCase.assertRaises,
            but checks that the message is right too.
        """
        try:
            callableObj(*args, **kwargs)
        except excClass:
            _, exc, _ = sys.exc_info()
            excMsg = str(exc)
            if not msg:
                # No message provided: it passes.
                return  #pragma: no cover
            elif excMsg == msg:
                # Message provided, and we got the right message: it passes.
                return
            else:   #pragma: no cover
                # Message provided, and it didn't match: fail!
                raise self.failureException(
                    "Right exception, wrong message: got '%s' expected '%s'" %
                    (excMsg, msg)
                    )
        # No need to catch other exceptions: They'll fail the test all by
        # themselves!
        else:   #pragma: no cover
            if hasattr(excClass,'__name__'):
                excName = excClass.__name__
            else:
                excName = str(excClass)
            raise self.failureException(
                "Expected to raise %s, didn't get an exception at all" %
                excName
                )

    def assert_equal_sets(self, s1, s2):
        """Assert that the two arguments are equal as sets."""
        self.assertEqual(set(s1), set(s2))

    def assert_matches(self, s, regex):
        """Assert that `s` matches `regex`."""
        m = re.search(regex, s)
        if not m:
            raise self.failureException("%r doesn't match %r" % (s, regex))

    def assert_multiline_equal(self, first, second):
        """Assert that two multi-line strings are equal.
        
        If they aren't, show a nice diff.
        
        """
        # Adapted from Py3.1 unittest.
        self.assert_(isinstance(first, str), (
                'First argument is not a string'))
        self.assert_(isinstance(second, str), (
                'Second argument is not a string'))

        if first != second:
            msg = ''.join(difflib.ndiff(first.splitlines(True),
                                                    second.splitlines(True)))
            self.fail("Multi-line strings are unequal:\n" + msg)
