"""Tests for Coverage.py's code parsing."""

import os, sys, textwrap

sys.path.insert(0, os.path.split(__file__)[0]) # Force relative import for Py3k
from coveragetest import CoverageTest

from coverage.parser import CodeParser


class ParserTest(CoverageTest):
    """Tests for Coverage.py's code parsing."""

    run_in_temp_dir = False

    def parse_source(self, text):
        """Parse `text` as source, and return the `CodeParser` used."""
        text = textwrap.dedent(text)
        cp = CodeParser(text, exclude="nocover")
        cp.parse_source()
        return cp
    
    def test_exit_counts(self):
        cp = self.parse_source("""\
            # check some basic branch counting
            class Foo:
                def foo(self, a):
                    if a:
                        return 5
                    else:
                        return 7
            
            class Bar:
                pass
            """)
        self.assertEqual(cp.exit_counts(), {
            2:1, 3:1, 4:2, 5:1, 7:1, 9:1, 10:1
            })

    def test_try_except(self):
        cp = self.parse_source("""\
            try:
                a = 2
            except ValueError:
                a = 4
            except ZeroDivideError:
                a = 6
            except:
                a = 8
            b = 9
            """)
        self.assertEqual(cp.exit_counts(), {
            1: 1, 2:1, 3:1, 4:1, 5:1, 6:1, 7:1, 8:1, 9:1
            })
    
    def test_excluded_classes(self):
        cp = self.parse_source("""\
            class Foo:
                def __init__(self):
                    pass
                    
            if 0:   # nocover
                class Bar:
                    pass
            """)
        self.assertEqual(cp.exit_counts(), {
            1:1, 2:1, 3:1
            })
        
    def XXX_missing_branch_to_excluded_code(self):
        cp = self.parse_source("""\
            if fooey:
                a = 2
            else:   # nocover
                a = 4
            b = 5
            """)
        self.assertEqual(cp.exit_counts(), { 1:1, 2:1, 5:1 })
        cp = self.parse_source("""\
            def foo():
                if fooey:
                    a = 3
                else:
                    a = 5
            b = 6
            """)
        self.assertEqual(cp.exit_counts(), { 1:1, 2:2, 3:1, 5:1, 6:1 })
        cp = self.parse_source("""\
            def foo():
                if fooey:
                    a = 3
                else:   # nocover
                    a = 5
            b = 6
            """)
        self.assertEqual(cp.exit_counts(), { 1:13, 2:1, 6:1 })
