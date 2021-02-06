# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Tests that our version shims in backward.py are working."""

import unittest

from coverage.backward import iitems, binary_bytes, bytes_to_ints

from tests.helpers import assert_count_equal

class BackwardTest(unittest.TestCase):
    """Tests of things from backward.py."""

    def test_iitems(self):
        d = {'a': 1, 'b': 2, 'c': 3}
        items = [('a', 1), ('b', 2), ('c', 3)]
        assert_count_equal(list(iitems(d)), items)

    def test_binary_bytes(self):
        byte_values = [0, 255, 17, 23, 42, 57]
        bb = binary_bytes(byte_values)
        assert len(bb) == len(byte_values)
        assert byte_values == list(bytes_to_ints(bb))
