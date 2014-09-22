"""Tests that our version shims in backward.py are working."""

from coverage.backunittest import TestCase
from coverage.backward import iitems, binary_bytes, byte_to_int, bytes_to_ints


class BackwardTest(TestCase):
    """Tests of things from backward.py."""

    def test_iitems(self):
        d = {'a': 1, 'b': 2, 'c': 3}
        items = [('a', 1), ('b', 2), ('c', 3)]
        self.assertCountEqual(list(iitems(d)), items)

    def test_binary_bytes(self):
        byte_values = [0, 255, 17, 23, 42, 57]
        bb = binary_bytes(byte_values)
        self.assertEqual(len(bb), len(byte_values))
        self.assertEqual(byte_values, list(bytes_to_ints(bb)))
        self.assertEqual(byte_values, [byte_to_int(b) for b in bb])
