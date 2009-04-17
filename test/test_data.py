"""Tests for coverage.data"""

import unittest
from coverage.data import CoverageData

class DataTest(unittest.TestCase):
    def test_reading(self):
        covdata = CoverageData()
        covdata.read()
        self.assertEqual(covdata.summary(), {})
