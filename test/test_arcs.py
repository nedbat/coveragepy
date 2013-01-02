"""Tests for Coverage.py's arc measurement."""

import sys
from test.coveragetest import CoverageTest


class SimpleArcTest(CoverageTest):
    """Tests for Coverage.py's arc measurement."""

    def test_simple_sequence(self):
        self.check_coverage("""\
            a = 1
            b = 2
            """,
            arcz=".1 12 2.")
        self.check_coverage("""\
            a = 1

            b = 3
            """,
            arcz=".1 13 3.")
        self.check_coverage("""\

            a = 2
            b = 3

            c = 5
            """,
            arcz=".2 23 35 5-2")

    def test_function_def(self):
        self.check_coverage("""\
            def foo():
                a = 2

            foo()
            """,
            arcz=".1 .2 14 2. 4.")

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

    def test_compact_if(self):
        self.check_coverage("""\
            a = 1
            if len([]) == 0: a = 2
            assert a == 2
            """,
            arcz=".1 12 23 3.", arcz_missing="")
        self.check_coverage("""\
            def fn(x):
                if x % 2: return True
                return False
            a = fn(1)
            assert a == True
            """,
            arcz=".1 14 45 5.  .2 2. 23 3.", arcz_missing="23 3.")

    def test_multiline(self):
        # The firstlineno of the a assignment below differs among Python
        # versions.
        if sys.version_info >= (2, 5):
            arcz = ".1 15 5-2"
        else:
            arcz = ".1 15 5-1"
        self.check_coverage("""\
            a = (
                2 +
                3
                )
            b = \\
                6
            """,
            arcz=arcz, arcz_missing="")

    def test_if_return(self):
        self.check_coverage("""\
            def if_ret(a):
                if a:
                    return 3
                b = 4
                return 5
            x = if_ret(0) + if_ret(1)
            assert x == 8
            """,
            arcz=".1 16 67 7.   .2 23 24 3. 45 5.", arcz_missing=""
            )

    def test_dont_confuse_exit_and_else(self):
        self.check_coverage("""\
            def foo():
                if foo:
                    a = 3
                else:
                    a = 5
                return a
            assert foo() == 3 # 7
            """,
            arcz=".1 17 7.  .2 23 36 25 56 6.", arcz_missing="25 56"
            )
        self.check_coverage("""\
            def foo():
                if foo:
                    a = 3
                else:
                    a = 5
            foo() # 6
            """,
            arcz=".1 16 6.  .2 23 3. 25 5.", arcz_missing="25 5."
            )

    if 0:   # expected failure
        def test_lambdas_are_confusing_bug_90(self):
            self.check_coverage("""\
                fn = lambda x: x
                a = 1
                """,
                arcz=".1 12 2."
                )


if sys.version_info >= (2, 6):
    class WithTest(CoverageTest):
        """Arc-measuring tests involving context managers."""

        def test_with(self):
            self.check_coverage("""\
                def example():
                    with open("test", "w") as f: # exit
                        f.write("")
                        return 1

                example()
                """,
                arcz=".1 .2 23 34 4. 16 6."
                )


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

    def test_while_true(self):
        # With "while 1", the loop knows it's constant.
        self.check_coverage("""\
            a, i = 1, 0
            while 1:
                if i >= 3:
                    a = 4
                    break
                i += 1
            assert a == 4 and i == 3
            """,
            arcz=".1 12 23 34 45 36 63 57 7.",
            )
        # With "while True", 2.x thinks it's computation, 3.x thinks it's
        # constant.
        if sys.version_info >= (3, 0):
            arcz = ".1 12 23 34 45 36 63 57 7."
        else:
            arcz = ".1 12 23 27 34 45 36 62 57 7."
        self.check_coverage("""\
            a, i = 1, 0
            while True:
                if i >= 3:
                    a = 4
                    break
                i += 1
            assert a == 4 and i == 3
            """,
            arcz=arcz,
            )

    def test_for_if_else_for(self):
        self.check_coverage("""\
            def branches_2(l):
                if l:
                    for e in l:
                        a = 4
                else:
                    a = 6

            def branches_3(l):
                for x in l:
                    if x:
                        for e in l:
                            a = 12
                    else:
                        a = 14

            branches_2([0,1])
            branches_3([0,1])
            """,
            arcz=
                ".1 18 8G GH H. "
                ".2 23 34 43 26 3. 6. "
                ".9 9A 9-8 AB BC CB B9 AE E9",
            arcz_missing="26 6."
            )

    def test_for_else(self):
        self.check_coverage("""\
            def forelse(seq):
                for n in seq:
                    if n > 5:
                        break
                else:
                    print('None of the values were greater than 5')
                print('Done')
            forelse([1,2])
            forelse([1,6])
            """,
            arcz=".1 .2 23 32 34 47 26 67 7. 18 89 9."
            )

    if 0:   # expected failure
        def test_confusing_for_loop_bug_175(self):
            self.check_coverage("""\
                o = [(1,2), (3,4)]
                o = [a for a in o if a[0] > 1]
                for tup in o:
                    x = tup[0]
                    y = tup[1]
                """,
                arcz=".1 12 23 34 45 53 3.",
                arcz_missing="", arcz_unpredicted="")
            self.check_coverage("""\
                o = [(1,2), (3,4)]
                for tup in [a for a in o if a[0] > 1]:
                    x = tup[0]
                    y = tup[1]
                """,
                arcz=".1 12 23 34 42 2.",
                arcz_missing="", arcz_unpredicted="")


class ExceptionArcTest(CoverageTest):
    """Arc-measuring tests involving exception handling."""

    def test_try_except(self):
        self.check_coverage("""\
            a, b = 1, 1
            try:
                a = 3
            except:
                b = 5
            assert a == 3 and b == 1
            """,
            arcz=".1 12 23 36 45 56 6.", arcz_missing="45 56")
        self.check_coverage("""\
            a, b = 1, 1
            try:
                a = 3
                raise Exception("Yikes!")
                a = 5
            except:
                b = 7
            assert a == 3 and b == 7
            """,
            arcz=".1 12 23 34 58 67 78 8.",
            arcz_missing="58", arcz_unpredicted="46")

    def test_hidden_raise(self):
        self.check_coverage("""\
            a, b = 1, 1
            def oops(x):
                if x % 2: raise Exception("odd")
            try:
                a = 5
                oops(1)
                a = 7
            except:
                b = 9
            assert a == 5 and b == 9
            """,
            arcz=".1 12 .3 3-2 24 45 56 67 7A 89 9A A.",
            arcz_missing="67 7A", arcz_unpredicted="68")

    def test_except_with_type(self):
        self.check_coverage("""\
            a, b = 1, 1
            def oops(x):
                if x % 2: raise ValueError("odd")
            def try_it(x):
                try:
                    a = 6
                    oops(x)
                    a = 8
                except ValueError:
                    b = 10
                return a
            assert try_it(0) == 8   # C
            assert try_it(1) == 6   # D
            """,
            arcz=".1 12 .3 3-2 24 4C CD D. .5 56 67 78 8B 9A AB B-4",
            arcz_missing="",
            arcz_unpredicted="79")

    def test_try_finally(self):
        self.check_coverage("""\
            a, c = 1, 1
            try:
                a = 3
            finally:
                c = 5
            assert a == 3 and c == 5
            """,
            arcz=".1 12 23 35 56 6.", arcz_missing="")
        self.check_coverage("""\
            a, c, d = 1, 1, 1
            try:
                try:
                    a = 4
                finally:
                    c = 6
            except:
                d = 8
            assert a == 4 and c == 6 and d == 1    # 9
            """,
            arcz=".1 12 23 34 46 67 78 89 69 9.",
            arcz_missing="67 78 89", arcz_unpredicted="")
        self.check_coverage("""\
            a, c, d = 1, 1, 1
            try:
                try:
                    a = 4
                    raise Exception("Yikes!")
                    a = 6
                finally:
                    c = 8
            except:
                d = 10                              # A
            assert a == 4 and c == 8 and d == 10    # B
            """,
            arcz=".1 12 23 34 45 68 89 8B 9A AB B.",
            arcz_missing="68 8B", arcz_unpredicted="58")

    def test_finally_in_loop(self):
        self.check_coverage("""\
            a, c, d, i = 1, 1, 1, 99
            try:
                for i in range(5):
                    try:
                        a = 5
                        if i > 0:
                            raise Exception("Yikes!")
                        a = 8
                    finally:
                        c = 10
            except:
                d = 12                              # C
            assert a == 5 and c == 10 and d == 12   # D
            """,
            arcz=".1 12 23 34 3D 45 56 67 68 8A A3 AB AD BC CD D.",
            arcz_missing="3D AD", arcz_unpredicted="7A")
        self.check_coverage("""\
            a, c, d, i = 1, 1, 1, 99
            try:
                for i in range(5):
                    try:
                        a = 5
                        if i > 10:
                            raise Exception("Yikes!")
                        a = 8
                    finally:
                        c = 10
            except:
                d = 12                              # C
            assert a == 8 and c == 10 and d == 1    # D
            """,
            arcz=".1 12 23 34 3D 45 56 67 68 8A A3 AB AD BC CD D.",
            arcz_missing="67 AB AD BC CD", arcz_unpredicted="")


    def test_break_in_finally(self):
        self.check_coverage("""\
            a, c, d, i = 1, 1, 1, 99
            try:
                for i in range(5):
                    try:
                        a = 5
                        if i > 0:
                            break
                        a = 8
                    finally:
                        c = 10
            except:
                d = 12                              # C
            assert a == 5 and c == 10 and d == 1    # D
            """,
            arcz=".1 12 23 34 3D 45 56 67 68 7A 8A A3 AB AD BC CD D.",
            arcz_missing="3D AB BC CD", arcz_unpredicted="")

    if 0:   # expected failure
        def test_finally_in_loop_2(self):
            self.check_coverage("""\
                for i in range(5):
                    try:
                        j = 3
                    finally:
                        f = 5
                    g = 6
                h = 7
                """,
                arcz=".1 12 23 35 56 61 17 7.",
                arcz_missing="", arcz_unpredicted="")

    if sys.version_info >= (2, 5):
        # Try-except-finally was new in 2.5
        def test_except_finally(self):
            self.check_coverage("""\
                a, b, c = 1, 1, 1
                try:
                    a = 3
                except:
                    b = 5
                finally:
                    c = 7
                assert a == 3 and b == 1 and c == 7
                """,
                arcz=".1 12 23 45 37 57 78 8.", arcz_missing="45 57")
            self.check_coverage("""\
                a, b, c = 1, 1, 1
                def oops(x):
                    if x % 2: raise Exception("odd")
                try:
                    a = 5
                    oops(1)
                    a = 7
                except:
                    b = 9
                finally:
                    c = 11
                assert a == 5 and b == 9 and c == 11
                """,
                arcz=".1 12 .3 3-2 24 45 56 67 7B 89 9B BC C.",
                arcz_missing="67 7B", arcz_unpredicted="68")


class MiscArcTest(CoverageTest):
    """Miscellaneous arc-measuring tests."""

    def test_dict_literal(self):
        self.check_coverage("""\
            d = {
                'a': 2,
                'b': 3,
                'c': {
                    'd': 5,
                    'e': 6,
                    }
                }
            assert d
            """,
            arcz=".1 19 9.")


class ExcludeTest(CoverageTest):
    """Tests of exclusions to indicate known partial branches."""

    def test_default(self):
        # A number of forms of pragma comment are accepted.
        self.check_coverage("""\
            a = 1
            if a:   #pragma: no branch
                b = 3
            c = 4
            if c:   # pragma NOBRANCH
                d = 6
            e = 7
            """,
            [1,2,3,4,5,6,7],
            arcz=".1 12 23 24 34 45 56 57 67 7.", arcz_missing="")

    def test_custom_pragmas(self):
        self.check_coverage("""\
            a = 1
            while a:    # [only some]
                c = 3
                break
            assert c == 5-2
            """,
            [1,2,3,4,5],
            partials=["only some"],
            arcz=".1 12 23 34 45 25 5.", arcz_missing="")
