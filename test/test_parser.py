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
        cp = CodeParser(text=text, exclude="nocover")
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
            1:0, 2:1, 3:1
            })

    def test_missing_branch_to_excluded_code(self):
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
        self.assertEqual(cp.exit_counts(), { 1:1, 2:1, 3:1, 6:1 })


class ParserFileTest(CoverageTest):
    """Tests for Coverage.py's code parsing from files."""

    def parse_file(self, filename):
        """Parse `text` as source, and return the `CodeParser` used."""
        cp = CodeParser(filename=filename, exclude="nocover")
        cp.parse_source()
        return cp

    def test_line_endings(self):
        text = """\
            # check some basic branch counting
            class Foo:
                def foo(self, a):
                    if a:
                        return 5
                    else:
                        return 7

            class Bar:
                pass
            """
        counts = { 2:1, 3:1, 4:2, 5:1, 7:1, 9:1, 10:1 }
        name_endings = (("unix", "\n"), ("dos", "\r\n"), ("mac", "\r"))
        for fname, newline in name_endings:
            fname = fname + ".py"
            self.make_file(fname, text, newline=newline)
            cp = self.parse_file(fname)
            self.assertEqual(cp.exit_counts(), counts)

    def test_encoding(self):
        self.make_file("encoded.py", """\
            coverage = "\xe7\xf6v\xear\xe3g\xe9"
            """)
        cp = self.parse_file("encoded.py")
        cp.exit_counts()
