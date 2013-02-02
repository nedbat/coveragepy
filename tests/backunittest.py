"""Implementations of unittest features from the future."""

import difflib, re, sys, unittest

from coverage.backward import set                   # pylint: disable=W0622


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

    if _need('assertIn'):
        def assertIn(self, member, container, msg=None):
            """Assert that `member` is in `container`."""
            if member not in container:
                msg = msg or ('%r not found in %r' % (member, container))
                self.fail(msg)

    if _need('assertNotIn'):
        def assertNotIn(self, member, container, msg=None):
            """Assert that `member` is not in `container`."""
            if member in container:
                msg = msg or ('%r found in %r' % (member, container))
                self.fail(msg)

    if _need('assertGreater'):
        def assertGreater(self, a, b, msg=None):
            """Assert that `a` is greater than `b`."""
            if not a > b:
                msg = msg or ('%r not greater than %r' % (a, b))
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
                else:
                    # Message provided, and it didn't match: fail!
                    raise self.failureException(
                        "Right exception, wrong message: "
                            "%r doesn't match %r" % (excMsg, regexp)
                        )
            # No need to catch other exceptions: They'll fail the test all by
            # themselves!
            else:
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
        def assertRegexpMatches(self, text, regex, msg=None):
            """Assert that `text` matches `regex`."""
            m = re.search(regex, text)
            if not m:
                msg = msg or ("%r doesn't match %r" % (text, regex))
                raise self.failureException(msg)

    if _need('assertMultiLineEqual'):
        def assertMultiLineEqual(self, first, second, msg=None):
            """Assert that two multi-line strings are equal.

            If they aren't, show a nice diff.

            """
            # Adapted from Py3.1 unittest.
            self.assertTrue(isinstance(first, str),
                    'First argument is not a string')
            self.assertTrue(isinstance(second, str),
                    'Second argument is not a string')

            if first != second:
                message = ''.join(difflib.ndiff(first.splitlines(True),
                                                    second.splitlines(True)))
                if msg:
                    message += " : " + msg
                self.fail("Multi-line strings are unequal:\n" + message)
