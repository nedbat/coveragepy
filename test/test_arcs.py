"""Tests for Coverage.py's arc measurement."""

import os, re, sys, textwrap

import coverage
from coverage.backward import StringIO

sys.path.insert(0, os.path.split(__file__)[0]) # Force relative import for Py3k
from coveragetest import CoverageTest


class ArcTest(CoverageTest):
    """Tests for Coverage.py's arc measurement."""

    def test_simple_sequence(self):
        self.check_coverage("""\
            a = 1
            b = 2
            """,
            arcs=[(-1,1), (1,2), (2,-1)], arcs_missing=[])
        self.check_coverage("""\
            a = 1

            b = 3
            """,
            arcs=[(-1,1), (1,3), (3,-1)], arcs_missing=[])
        self.check_coverage("""\

            a = 2
            b = 3
            
            c = 5
            """,
            arcs=[(-1,2), (2,3), (3,5),(5,-1)], arcs_missing=[])

    def test_function_def(self):
        self.check_coverage("""\
            def foo():
                a = 2
                
            foo()
            """,
            arcs=[(-1,1), (-1,2),(1,4),(2,-1), (4,-1)], arcs_missing=[])

    def test_if(self):
        self.check_coverage("""\
            a = 1
            if len([]) == 0:
                a = 3
            assert a == 3
            """,
            arcz=".1 12 23 24 34 4.", arcz_missing="24")
        self.check_coverage("""\
            a = 1
            if len([]) == 1:
                a = 3
            assert a == 1
            """,
            arcz=".1 12 23 24 34 4.", arcz_missing="23 34")
        
    def test_if_else(self):
        self.check_coverage("""\
            if len([]) == 0:
                a = 2
            else:
                b = 4
            c = 5
            """,
            arcz=".1 12 25 14 45 5.", arcz_missing="14 45")
        self.check_coverage("""\
            if len([]) == 1:
                a = 2
            else:
                b = 4
            c = 5
            """,
            arcz=".1 12 25 14 45 5.", arcz_missing="12 25")
        
    def test_loop(self):
        self.check_coverage("""\
            for i in range(10):
                a = 2
            b = 3
            """,
            arcz=".1 12 21 13 3.", arcz_missing="")
        self.check_coverage("""\
            for i in range(0):
                a = 2
            b = 3
            """,
            arcz=".1 12 21 13 3.", arcz_missing="12 21")

    def xest_xx(self):
        self.check_coverage("""\
            """,
            arcz="", arcz_missing="")
