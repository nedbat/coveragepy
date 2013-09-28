# -*- coding: utf-8 -*-
"""Tests that our version shims in backward.py are working."""

from coverage.backward import iitems
from tests.backunittest import TestCase


class BackwardTest(TestCase):
    """Tests of things from backward.py."""

    run_in_temp_dir = False

    def test_iitems(self):
        d = {'a': 1, 'b': 2, 'c': 3}
        items = [('a', 1), ('b', 2), ('c', 3)]
        self.assertSameElements(list(iitems(d)), items)
