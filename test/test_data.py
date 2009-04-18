"""Tests for coverage.data"""

from coverage.data import CoverageData
from coveragetest import CoverageTest

class DataTest(CoverageTest):
    def test_reading(self):
        covdata = CoverageData()
        covdata.read()
        self.assertEqual(covdata.summary(), {})
