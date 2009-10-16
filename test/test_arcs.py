"""Tests for Coverage.py's arc measurement."""

import os, re, sys, textwrap

import coverage
from coverage.backward import StringIO

sys.path.insert(0, os.path.split(__file__)[0]) # Force relative import for Py3k
from coveragetest import CoverageTest


class SimpleArcTest(CoverageTest):
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
                a = 4
            assert a == 2
            """,
            arcz=".1 12 25 14 45 5.", arcz_missing="14 45")
        self.check_coverage("""\
            if len([]) == 1:
                a = 2
            else:
                a = 4
            assert a == 4
            """,
            arcz=".1 12 25 14 45 5.", arcz_missing="12 25")
        
class LoopArcTest(CoverageTest):
    """Arc-measuring tests involving loops."""
    
    def test_loop(self):
        self.check_coverage("""\
            for i in range(10):
                a = i
            assert a == 9
            """,
            arcz=".1 12 21 13 3.", arcz_missing="")
        self.check_coverage("""\
            a = -1
            for i in range(0):
                a = i
            assert a == -1
            """,
            arcz=".1 12 23 32 24 4.", arcz_missing="23 32")

    def test_nested_loop(self):
        self.check_coverage("""\
            for i in range(3):
                for j in range(3):
                    a = i + j
            assert a == 4
            """,
            arcz=".1 12 23 32 21 14 4.", arcz_missing="")

    def test_break(self):
        self.check_coverage("""\
            for i in range(10):
                a = i
                break       # 3
                a = 99
            assert a == 0   # 5
            """,
            arcz=".1 12 23 35 15 41 5.", arcz_missing="15 41")

    def test_continue(self):
        self.check_coverage("""\
            for i in range(10):
                a = i
                continue    # 3
                a = 99
            assert a == 9   # 5
            """,
            arcz=".1 12 23 31 15 41 5.", arcz_missing="41")

    def test_nested_breaks(self):
        self.check_coverage("""\
            for i in range(3):
                for j in range(3):
                    a = i + j
                    break               # 4
                if i == 2:
                    break
            assert a == 2 and i == 2    # 7
            """,
            arcz=".1 12 23 34 45 25 56 51 67 17 7.", arcz_missing="17 25")
        
    def xest_xx(self):
        self.check_coverage("""\
            """,
            arcz="", arcz_missing="")
