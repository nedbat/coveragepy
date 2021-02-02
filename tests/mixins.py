# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""
Test class mixins

Some of these are transitional while working toward pure-pytest style.
"""

import functools
import types

from coverage.backunittest import unittest
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
