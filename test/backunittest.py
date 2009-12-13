"""Implementations of unittest features from the future."""

import difflib, re, sys, unittest

from coverage.backward import set                   # pylint: disable-msg=W0622


def _need(method):
    """Do we need to define our own `method` method?"""
    return not hasattr(unittest.TestCase, method)


class TestCase(unittest.TestCase):
    """Just like unittest.TestCase, but with assert methods added.

    Designed to be compatible with 3.1 unittest.  Methods are only defined if
    the builtin `unittest` doesn't have them.

    """
    if _need('assertTrue'):
        def assertTrue(self, exp, msg=None):
            """Assert that `exp` is true."""
            if not exp:
                self.fail(msg)

    if _need('assertFalse'):
        def assertFalse(self, exp, msg=None):
            """Assert that `exp` is false."""
            if exp:
                self.fail(msg)

    if _need('assertRaisesRegexp'):
        def assertRaisesRegexp(self, excClass, regexp, callobj, *args, **kw):
            """ Just like unittest.TestCase.assertRaises,
                but checks that the message is right too.
            """
            try:
                callobj(*args, **kw)
            except excClass:
                _, exc, _ = sys.exc_info()
                excMsg = str(exc)
                if re.search(regexp, excMsg):
                    # Message provided, and we got the right one: it passes.
                    return
                else:   #pragma: no cover
                    # Message provided, and it didn't match: fail!
                    raise self.failureException(
                        "Right exception, wrong message: "
                            "'%s' doesn't match '%s'" % (excMsg, regexp)
                        )
            # No need to catch other exceptions: They'll fail the test all by
            # themselves!
            else:   #pragma: no cover
                if hasattr(excClass, '__name__'):
                    excName = excClass.__name__
                else:
                    excName = str(excClass)
                raise self.failureException(
                    "Expected to raise %s, didn't get an exception at all" %
                    excName
                    )

    if _need('assertSameElements'):
        def assertSameElements(self, s1, s2):
            """Assert that the two arguments are equal as sets."""
            self.assertEqual(set(s1), set(s2))

    if _need('assertRegexpMatches'):
        def assertRegexpMatches(self, s, regex):
            """Assert that `s` matches `regex`."""
            m = re.search(regex, s)
            if not m:
                raise self.failureException("%r doesn't match %r" % (s, regex))

    if _need('assertMultiLineEqual'):
        def assertMultiLineEqual(self, first, second):
            """Assert that two multi-line strings are equal.

            If they aren't, show a nice diff.

            """
            # Adapted from Py3.1 unittest.
            self.assertTrue(isinstance(first, str),
                    'First argument is not a string')
            self.assertTrue(isinstance(second, str),
                    'Second argument is not a string')

            if first != second:
                msg = ''.join(difflib.ndiff(first.splitlines(True),
                                                    second.splitlines(True)))
                self.fail("Multi-line strings are unequal:\n" + msg)
