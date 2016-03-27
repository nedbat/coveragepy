# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

"""Tests for coverage.py's code parsing."""

import textwrap

from tests.coveragetest import CoverageTest

from coverage import env
from coverage.misc import NotPython
from coverage.parser import PythonParser


class PythonParserTest(CoverageTest):
    """Tests for coverage.py's Python code parsing."""

    run_in_temp_dir = False

    def parse_source(self, text):
        """Parse `text` as source, and return the `PythonParser` used."""
        if env.PY2:
            text = text.decode("ascii")
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
        # https://bitbucket.org/ned/coveragepy/issue/324/yield-in-loop-confuses-branch-coverage
        parser = self.parse_source("""\
            def gen(input):
                for n in inp:
                    yield (i * 2 for i in range(n))

            list(gen([1,2,3]))
            """)
        self.assertEqual(parser.exit_counts(), {
            1:1,    # def -> list
            2:2,    # for -> yield; for -> exit
            3:2,    # yield -> for;  genexp exit
            5:1,    # list -> exit
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
            1: 1, 2:1, 3:2, 4:1, 5:2, 6:1, 7:1, 8:1, 9:1
            })

    def test_excluded_classes(self):
        parser = self.parse_source("""\
            class Foo:
                def __init__(self):
                    pass

            if len([]):     # nocover
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

    def test_indentation_error(self):
        msg = (
            "Couldn't parse '<code>' as Python source: "
            "'unindent does not match any outer indentation level' at line 3"
        )
        with self.assertRaisesRegex(NotPython, msg):
            _ = self.parse_source("""\
                0 spaces
                  2
                 1
                """)

    def test_token_error(self):
        msg = "Couldn't parse '<code>' as Python source: 'EOF in multi-line string' at line 1"
        with self.assertRaisesRegex(NotPython, msg):
            _ = self.parse_source("""\
                '''
                """)

    def test_decorator_pragmas(self):
        parser = self.parse_source("""\
            # 1

            @foo(3)                     # nocover
            @bar
            def func(x, y=5):
                return 6

            class Foo:      # this is the only statement.
                '''9'''
                @foo                    # nocover
                def __init__(self):
                    '''12'''
                    return 13

                @foo(                   # nocover
                    16,
                    17,
                )
                def meth(self):
                    return 20

            @foo(                       # nocover
                23
            )
            def func(x=25):
                return 26
            """)
        self.assertEqual(
            parser.raw_statements,
            set([3, 4, 5, 6, 8, 9, 10, 13, 15, 16, 17, 20, 22, 23, 25, 26])
        )
        self.assertEqual(parser.statements, set([8]))

    def test_class_decorator_pragmas(self):
        parser = self.parse_source("""\
            class Foo(object):
                def __init__(self):
                    self.x = 3

            @foo                        # nocover
            class Bar(object):
                def __init__(self):
                    self.x = 8
            """)
        self.assertEqual(parser.raw_statements, set([1, 2, 3, 5, 6, 7, 8]))
        self.assertEqual(parser.statements, set([1, 2, 3]))


class ParserMissingArcDescriptionTest(CoverageTest):
    """Tests for PythonParser.missing_arc_description."""

    run_in_temp_dir = False

    def parse_text(self, source):
        """Parse Python source, and return the parser object."""
        parser = PythonParser(textwrap.dedent(source))
        parser.parse_source()
        return parser

    def test_missing_arc_description(self):
        # This code is never run, so the actual values don't matter.
        parser = self.parse_text(u"""\
            if x:
                print(2)
            print(3)

            def func5():
                for x in range(6):
                    if x == 7:
                        break

            def func10():
                while something(11):
                    thing(12)
                more_stuff(13)
            """)
        self.assertEqual(
            parser.missing_arc_description(1, 2),
            "line 1 didn't jump to line 2, because the condition on line 1 was never true"
        )
        self.assertEqual(
            parser.missing_arc_description(1, 3),
            "line 1 didn't jump to line 3, because the condition on line 1 was never false"
        )
        self.assertEqual(
            parser.missing_arc_description(6, -5),
            "line 6 didn't return from function 'func5', "
                            "because the loop on line 6 didn't complete"
        )
        self.assertEqual(
            parser.missing_arc_description(6, 7),
            "line 6 didn't jump to line 7, because the loop on line 6 never started"
        )
        self.assertEqual(
            parser.missing_arc_description(11, 12),
            "line 11 didn't jump to line 12, because the condition on line 11 was never true"
        )
        self.assertEqual(
            parser.missing_arc_description(11, 13),
            "line 11 didn't jump to line 13, because the condition on line 11 was never false"
        )

    def test_missing_arc_descriptions_for_small_callables(self):
        # We use 2.7 features here, so just skip this test on 2.6
        if env.PYVERSION < (2, 7):
            self.skip("No dict or set comps in 2.6")

        parser = self.parse_text(u"""\
            callables = [
                lambda: 2,
                (x for x in range(3)),
                {x:1 for x in range(4)},
                {x for x in range(5)},
            ]
            x = 7
            """)
        self.assertEqual(
            parser.missing_arc_description(2, -2),
            "line 2 didn't finish the lambda on line 2"
        )
        self.assertEqual(
            parser.missing_arc_description(3, -3),
            "line 3 didn't finish the generator expression on line 3"
        )
        self.assertEqual(
            parser.missing_arc_description(4, -4),
            "line 4 didn't finish the dictionary comprehension on line 4"
        )
        self.assertEqual(
            parser.missing_arc_description(5, -5),
            "line 5 didn't finish the set comprehension on line 5"
        )

    def test_missing_arc_descriptions_for_exceptions(self):
        parser = self.parse_text(u"""\
            try:
                pass
            except ZeroDivideError:
                print("whoops")
            except ValueError:
                print("yikes")
            """)
        self.assertEqual(
            parser.missing_arc_description(3, 4),
            "line 3 didn't jump to line 4, because the exception caught by line 3 didn't happen"
        )
        self.assertEqual(
            parser.missing_arc_description(5, 6),
            "line 5 didn't jump to line 6, because the exception caught by line 5 didn't happen"
        )

    def test_missing_arc_descriptions_for_finally(self):
        parser = self.parse_text(u"""\
            def function():
                for i in range(2):
                    try:
                        if something(4):
                            break
                        else:
                            if something(7):
                                continue
                            else:
                                continue
                        if also_this(11):
                            return 12
                        else:
                            raise Exception(14)
                    finally:
                        this_thing(16)
                that_thing(17)
            """)
        self.assertEqual(
            parser.missing_arc_description(16, 17),
            "line 16 didn't jump to line 17, because the break on line 5 wasn't executed"
        )
        self.assertEqual(
            parser.missing_arc_description(16, 2),
            "line 16 didn't jump to line 2, "
                "because the continue on line 8 wasn't executed"
                " or "
                "the continue on line 10 wasn't executed"
        )
        self.assertEqual(
            parser.missing_arc_description(16, -1),
            "line 16 didn't except from function 'function', "
                "because the raise on line 14 wasn't executed"
            " or "
            "line 16 didn't return from function 'function', "
                "because the return on line 12 wasn't executed"
        )

    def test_missing_arc_descriptions_bug460(self):
        parser = self.parse_text(u"""\
            x = 1
            d = {
                3: lambda: [],
                4: lambda: [],
            }
            x = 6
            """)
        self.assertEqual(
            parser.missing_arc_description(2, -3),
            "line 3 didn't finish the lambda on line 3",
        )


class ParserFileTest(CoverageTest):
    """Tests for coverage.py's code parsing from files."""

    def parse_file(self, filename):
        """Parse `text` as source, and return the `PythonParser` used."""
        parser = PythonParser(filename=filename, exclude="nocover")
        parser.parse_source()
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
            self.assertEqual(
                parser.exit_counts(),
                counts,
                "Wrong for %r" % fname
            )

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

        parser = self.parse_file("normal.py")
        self.assertEqual(parser.statements, set([1]))

        self.make_file("abrupt.py", """\
            out, err = subprocess.Popen(
                [sys.executable, '-c', 'pass'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE).communicate()""")   # no final newline.

        # Double-check that some test helper wasn't being helpful.
        with open("abrupt.py") as f:
            self.assertEqual(f.read()[-1], ")")

        parser = self.parse_file("abrupt.py")
        self.assertEqual(parser.statements, set([1]))
