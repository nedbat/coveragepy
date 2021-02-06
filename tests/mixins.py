# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""
Test class mixins

Some of these are transitional while working toward pure-pytest style.
"""

import functools
import types
import unittest

import pytest

from coverage.misc import StopEverything


def convert_skip_exceptions(method):
    """A decorator for test methods to convert StopEverything to SkipTest."""
    @functools.wraps(method)
    def _wrapper(*args, **kwargs):
        try:
            result = method(*args, **kwargs)
        except StopEverything:
            raise unittest.SkipTest("StopEverything!")
        return result
    return _wrapper


class SkipConvertingMetaclass(type):
    """Decorate all test methods to convert StopEverything to SkipTest."""
    def __new__(cls, name, bases, attrs):
        for attr_name, attr_value in attrs.items():
            if attr_name.startswith('test_') and isinstance(attr_value, types.FunctionType):
                attrs[attr_name] = convert_skip_exceptions(attr_value)

        return super(SkipConvertingMetaclass, cls).__new__(cls, name, bases, attrs)


StopEverythingMixin = SkipConvertingMetaclass('StopEverythingMixin', (), {})


class StdStreamCapturingMixin:
    """
    Adapter from the pytest capsys fixture to more convenient methods.

    This doesn't also output to the real stdout, so we probably want to move
    to "real" capsys when we can use fixtures in test methods.

    Once you've used one of these methods, the capturing is reset, so another
    invocation will only return the delta.

    """
    @pytest.fixture(autouse=True)
    def _capcapsys(self, capsys):
        """Grab the fixture so our methods can use it."""
        self.capsys = capsys

    def stdouterr(self):
        """Returns (out, err), two strings for stdout and stderr."""
        return self.capsys.readouterr()

    def stdout(self):
        """Returns a string, the captured stdout."""
        return self.capsys.readouterr().out

    def stderr(self):
        """Returns a string, the captured stderr."""
        return self.capsys.readouterr().err
