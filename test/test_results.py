"""Tests for Coverage.py's results analysis."""

import os, sys

from coverage.results import Numbers

sys.path.insert(0, os.path.split(__file__)[0]) # Force relative import for Py3k
from coveragetest import CoverageTest


class NumbersTest(CoverageTest):
    """Tests for Coverage.py's numeric measurement summaries."""
    
    run_in_temp_dir = False

    def test_basic(self):
        n1 = Numbers(n_files=1, n_statements=200, n_missing=20)
        self.assertEqual(n1.n_statements, 200)
        self.assertEqual(n1.n_executed, 180)
        self.assertEqual(n1.n_missing, 20)
        self.assertEqual(n1.pc_covered, 90)
        
    def test_addition(self):
        n1 = Numbers(n_files=1, n_statements=200, n_missing=20)
        n2 = Numbers(n_files=1, n_statements=10, n_missing=8)
        n3 = n1 + n2
        self.assertEqual(n3.n_files, 2)
        self.assertEqual(n3.n_statements, 210)
        self.assertEqual(n3.n_executed, 182)
        self.assertEqual(n3.n_missing, 28)
        self.assertAlmostEqual(n3.pc_covered, 86.666666666)

    def test_sum(self):
        n1 = Numbers(n_files=1, n_statements=200, n_missing=20)
        n2 = Numbers(n_files=1, n_statements=10, n_missing=8)
        n3 = sum([n1, n2])
        self.assertEqual(n3.n_files, 2)
        self.assertEqual(n3.n_statements, 210)
        self.assertEqual(n3.n_executed, 182)
        self.assertEqual(n3.n_missing, 28)
        self.assertAlmostEqual(n3.pc_covered, 86.666666666)
