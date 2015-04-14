"""Tests for Coverage.py's code parsing."""

import textwrap
from tests.coveragetest import CoverageTest
from coverage.parser import PythonParser


class PythonParserTest(CoverageTest):
    """Tests for Coverage.py's Python code parsing."""

    run_in_temp_dir = False

    def parse_source(self, text):
        """Parse `text` as source, and return the `PythonParser` used."""
        text = textwrap.dedent(text)
        parser = PythonParser(text=text, exclude="nocover")
        parser.parse_source()
        return parser

    def test_exit_counts(self):
        parser = self.parse_source("""\
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
        self.assertEqual(parser.exit_counts(), {
            2:1, 3:1, 4:2, 5:1, 7:1, 9:1, 10:1
            })

    def test_generator_exit_counts(self):
        parser = self.parse_source("""\
            # generators yield lines should only have one exit count
            def gen(input):
                for n in inp:
                    yield (i * 2 for i in range(n))

            list(gen([1,2,3]))
            """)
        self.assertEqual(parser.exit_counts(), {
           2:1, 3:2, 4:1, 6:1
        })

    def test_try_except(self):
        parser = self.parse_source("""\
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
        self.assertEqual(parser.exit_counts(), {
            1: 1, 2:1, 3:1, 4:1, 5:1, 6:1, 7:1, 8:1, 9:1
            })

    def test_excluded_classes(self):
        parser = self.parse_source("""\
            class Foo:
                def __init__(self):
                    pass

            if 0:   # nocover
                class Bar:
                    pass
            """)
        self.assertEqual(parser.exit_counts(), {
            1:0, 2:1, 3:1
            })

    def test_missing_branch_to_excluded_code(self):
        parser = self.parse_source("""\
            if fooey:
                a = 2
            else:   # nocover
                a = 4
            b = 5
            """)
        self.assertEqual(parser.exit_counts(), { 1:1, 2:1, 5:1 })
        parser = self.parse_source("""\
            def foo():
                if fooey:
                    a = 3
                else:
                    a = 5
            b = 6
            """)
        self.assertEqual(parser.exit_counts(), { 1:1, 2:2, 3:1, 5:1, 6:1 })
        parser = self.parse_source("""\
            def foo():
                if fooey:
                    a = 3
                else:   # nocover
                    a = 5
            b = 6
            """)
        self.assertEqual(parser.exit_counts(), { 1:1, 2:1, 3:1, 6:1 })


class ParserFileTest(CoverageTest):
    """Tests for Coverage.py's code parsing from files."""

    def parse_file(self, filename):
        """Parse `text` as source, and return the `PythonParser` used."""
        parser = PythonParser(filename=filename, exclude="nocover")
        self.statements, self.excluded = parser.parse_source()
        return parser

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
            parser = self.parse_file(fname)
            self.assertEqual(parser.exit_counts(), counts)

    def test_encoding(self):
        self.make_file("encoded.py", """\
            coverage = "\xe7\xf6v\xear\xe3g\xe9"
            """)
        parser = self.parse_file("encoded.py")
        self.assertEqual(parser.exit_counts(), {1: 1})

    def test_missing_line_ending(self):
        # Test that the set of statements is the same even if a final
        # multi-line statement has no final newline.
        # https://bitbucket.org/ned/coveragepy/issue/293

        self.make_file("normal.py", """\
            out, err = subprocess.Popen(
                [sys.executable, '-c', 'pass'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE).communicate()
            """)

        self.parse_file("normal.py")
        self.assertEqual(self.statements, set([1]))

        self.make_file("abrupt.py", """\
            out, err = subprocess.Popen(
                [sys.executable, '-c', 'pass'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE).communicate()""")   # no final newline.

        # Double-check that some test helper wasn't being helpful.
        with open("abrupt.py") as f:
            self.assertEqual(f.read()[-1], ")")

        self.parse_file("abrupt.py")
        self.assertEqual(self.statements, set([1]))
