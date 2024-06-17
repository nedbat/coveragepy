# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Tests for coverage.py's arc measurement."""

from __future__ import annotations

import pytest

from tests.coveragetest import CoverageTest
from tests.helpers import assert_count_equal, xfail_pypy38

import coverage
from coverage import env
from coverage.data import sorted_lines
from coverage.files import abs_file


# When a try block ends, does the finally block (incorrectly) jump to the
# last statement, or does it go the line outside the try block that it
# should?
xfail_pypy_3882 = pytest.mark.xfail(
    env.PYPY and env.PYVERSION[:2] == (3, 8) and env.PYPYVERSION >= (7, 3, 11),
    reason="https://foss.heptapod.net/pypy/pypy/-/issues/3882",
)

class SimpleArcTest(CoverageTest):
    """Tests for coverage.py's arc measurement."""

    def test_simple_sequence(self) -> None:
        self.check_coverage("""\
            a = 1
            b = 2
            """,
            arcz=".1 12 2.",
        )
        self.check_coverage("""\
            a = 1

            b = 3
            """,
            arcz=".1 13 3.",
        )
        line1 = 1 if env.PYBEHAVIOR.module_firstline_1 else 2
        self.check_coverage("""\

            a = 2
            b = 3

            c = 5
            """,
            arcz=f"-{line1}2 23 35 5-{line1}",
        )

    def test_function_def(self) -> None:
        self.check_coverage("""\
            def foo():
                a = 2

            foo()
            """,
            arcz=".1 .2 14 2. 4.",
        )

    def test_if(self) -> None:
        self.check_coverage("""\
            a = 1
            if len([]) == 0:
                a = 3
            assert a == 3
            """,
            arcz=".1 12 23 24 34 4.", arcz_missing="24",
        )
        self.check_coverage("""\
            a = 1
            if len([]) == 1:
                a = 3
            assert a == 1
            """,
            arcz=".1 12 23 24 34 4.", arcz_missing="23 34",
        )

    def test_if_else(self) -> None:
        self.check_coverage("""\
            if len([]) == 0:
                a = 2
            else:
                a = 4
            assert a == 2
            """,
            arcz=".1 12 25 14 45 5.", arcz_missing="14 45",
        )
        self.check_coverage("""\
            if len([]) == 1:
                a = 2
            else:
                a = 4
            assert a == 4
            """,
            arcz=".1 12 25 14 45 5.", arcz_missing="12 25",
        )

    def test_compact_if(self) -> None:
        self.check_coverage("""\
            a = 1
            if len([]) == 0: a = 2
            assert a == 2
            """,
            arcz=".1 12 23 3.",
        )
        self.check_coverage("""\
            def fn(x):
                if x % 2: return True
                return False
            a = fn(1)
            assert a is True
            """,
            arcz=".1 14 45 5.  .2 2. 23 3.", arcz_missing="23 3.",
        )

    def test_multiline(self) -> None:
        self.check_coverage("""\
            a = (
                2 +
                3
                )
            b = \\
                6
            """,
            arcz=".1 15 5.",
        )

    def test_if_return(self) -> None:
        self.check_coverage("""\
            def if_ret(a):
                if a:
                    return 3
                b = 4
                return 5
            x = if_ret(0) + if_ret(1)
            assert x == 8
            """,
            arcz=".1 16 67 7.   .2 23 24 3. 45 5.",
        )

    def test_dont_confuse_exit_and_else(self) -> None:
        self.check_coverage("""\
            def foo():
                if foo:
                    a = 3
                else:
                    a = 5
                return a
            assert foo() == 3 # 7
            """,
            arcz=".1 17 7.  .2 23 36 25 56 6.", arcz_missing="25 56",
        )
        self.check_coverage("""\
            def foo():
                if foo:
                    a = 3
                else:
                    a = 5
            foo() # 6
            """,
            arcz=".1 16 6.  .2 23 3. 25 5.", arcz_missing="25 5.",
        )

    def test_what_is_the_sound_of_no_lines_clapping(self) -> None:
        if env.PYBEHAVIOR.empty_is_empty:
            arcz_missing=".1 1."
        else:
            arcz_missing=""
        self.check_coverage("""\
            # __init__.py
            """,
            arcz=".1 1.",
            arcz_missing=arcz_missing,
        )

    def test_bug_1184(self) -> None:
        self.check_coverage("""\
            def foo(x):
                if x:
                    try:
                        1/(x - 1)
                    except ZeroDivisionError:
                        pass
                return x        # 7

            for i in range(3):  # 9
                foo(i)
            """,
            arcz=".1 19 9-1  .2 23 27 34 47 56 67 7-1  9A A9",
            arcz_unpredicted="45",
        )


class WithTest(CoverageTest):
    """Arc-measuring tests involving context managers."""

    def test_with(self) -> None:
        arcz = ".1 .2 23 34 4. 16 6."
        if env.PYBEHAVIOR.exit_through_with:
            arcz = arcz.replace("4.", "42 2.")
        self.check_coverage("""\
            def example():
                with open("test", "w") as f:
                    f.write("3")
                    a = 4

            example()
            """,
            arcz=arcz,
        )

    def test_with_return(self) -> None:
        arcz = ".1 .2 23 34 4. 16 6."
        if env.PYBEHAVIOR.exit_through_with:
            arcz = arcz.replace("4.", "42 2.")
        self.check_coverage("""\
            def example():
                with open("test", "w") as f:
                    f.write("3")
                    return 4

            example()
            """,
            arcz=arcz,
        )

    def test_bug_146(self) -> None:
        # https://github.com/nedbat/coveragepy/issues/146
        arcz = ".1 12 23 34 41 15 5."
        if env.PYBEHAVIOR.exit_through_with:
            arcz = arcz.replace("34", "32 24")
        self.check_coverage("""\
            for i in range(2):
                with open("test", "w") as f:
                    print(3)
                print(4)
            print(5)
            """,
            arcz=arcz,
        )

    def test_nested_with_return(self) -> None:
        arcz = ".1 .2 23 34 45 56 6. 18 8."
        if env.PYBEHAVIOR.exit_through_with:
            arcz = arcz.replace("6.", "64 42 2.")
        self.check_coverage("""\
            def example(x):
                with open("test", "w") as f2:
                    a = 3
                    with open("test2", "w") as f4:
                        f2.write("5")
                        return 6

            example(8)
            """,
            arcz=arcz,
        )

    def test_break_through_with(self) -> None:
        arcz = ".1 12 23 34 45 15 5."
        if env.PYBEHAVIOR.exit_through_with:
            arcz = arcz.replace("45", "42 25")
        self.check_coverage("""\
            for i in range(1+1):
                with open("test", "w") as f:
                    print(3)
                    break
            print(5)
            """,
            arcz=arcz,
            arcz_missing="15",
        )

    def test_continue_through_with(self) -> None:
        arcz = ".1 12 23 34 41 15 5."
        if env.PYBEHAVIOR.exit_through_with:
            arcz = arcz.replace("41", "42 21")
        self.check_coverage("""\
            for i in range(1+1):
                with open("test", "w") as f:
                    print(3)
                    continue
            print(5)
            """,
            arcz=arcz,
        )

    # https://github.com/nedbat/coveragepy/issues/1270
    def test_raise_through_with(self) -> None:
        if env.PYBEHAVIOR.exit_through_with:
            arcz = ".1 12 27 78 8. 9A A.  -23 34 45 53 6-2"
            arcz_missing = "6-2 8."
            arcz_unpredicted = "3-2 89"
        else:
            arcz = ".1 12 27 78 8. 9A A.  -23 34 45 5-2 6-2"
            arcz_missing = "6-2 8."
            arcz_unpredicted = "89"
        cov = self.check_coverage("""\
            from contextlib import suppress
            def f(x):
                with suppress():    # used as a null context manager
                    print(4)
                    raise Exception("Boo6")
                print(6)
            try:
                f(8)
            except Exception:
                print("oops 10")
            """,
            arcz=arcz,
            arcz_missing=arcz_missing,
            arcz_unpredicted=arcz_unpredicted,
        )
        expected = "line 3 didn't jump to the function exit"
        assert self.get_missing_arc_description(cov, 3, -2) == expected

    def test_untaken_raise_through_with(self) -> None:
        if env.PYBEHAVIOR.exit_through_with:
            arcz = ".1 12 28 89 9. AB B.  -23 34 45 56 53 63 37 7-2"
            arcz_missing = "56 63 AB B."
        else:
            arcz = ".1 12 28 89 9. AB B.  -23 34 45 56 6-2 57 7-2"
            arcz_missing = "56 6-2 AB B."
        cov = self.check_coverage("""\
            from contextlib import suppress
            def f(x):
                with suppress():    # used as a null context manager
                    print(4)
                    if x == 5:
                        raise Exception("Boo6")
                print(7)
            try:
                f(9)
            except Exception:
                print("oops 11")
            """,
            arcz=arcz,
            arcz_missing=arcz_missing,
        )
        expected = "line 3 didn't jump to the function exit"
        assert self.get_missing_arc_description(cov, 3, -2) == expected


class LoopArcTest(CoverageTest):
    """Arc-measuring tests involving loops."""

    def test_loop(self) -> None:
        self.check_coverage("""\
            for i in range(10):
                a = i
            assert a == 9
            """,
            arcz=".1 12 21 13 3.",
        )
        self.check_coverage("""\
            a = -1
            for i in range(0):
                a = i
            assert a == -1
            """,
            arcz=".1 12 23 32 24 4.", arcz_missing="23 32",
        )

    def test_nested_loop(self) -> None:
        self.check_coverage("""\
            for i in range(3):
                for j in range(3):
                    a = i + j
            assert a == 4
            """,
            arcz=".1 12 23 32 21 14 4.",
        )

    def test_break(self) -> None:
        if env.PYBEHAVIOR.omit_after_jump:
            arcz = ".1 12 23 35 15 5."
            arcz_missing = "15"
        else:
            arcz = ".1 12 23 35 15 41 5."
            arcz_missing = "15 41"

        self.check_coverage("""\
            for i in range(10):
                a = i
                break       # 3
                a = 99
            assert a == 0   # 5
            """,
            arcz=arcz, arcz_missing=arcz_missing,
        )

    def test_continue(self) -> None:
        if env.PYBEHAVIOR.omit_after_jump:
            arcz = ".1 12 23 31 15 5."
            arcz_missing = ""
        else:
            arcz = ".1 12 23 31 15 41 5."
            arcz_missing = "41"

        self.check_coverage("""\
            for i in range(10):
                a = i
                continue    # 3
                a = 99
            assert a == 9   # 5
            """,
            arcz=arcz, arcz_missing=arcz_missing,
        )

    def test_nested_breaks(self) -> None:
        self.check_coverage("""\
            for i in range(3):
                for j in range(3):
                    a = i + j
                    break               # 4
                if i == 2:
                    break
            assert a == 2 and i == 2    # 7
            """,
            arcz=".1 12 23 34 45 25 56 51 67 17 7.", arcz_missing="17 25",
        )

    def test_while_1(self) -> None:
        # With "while 1", the loop knows it's constant.
        if env.PYBEHAVIOR.keep_constant_test:
            arcz = ".1 12 23 34 45 36 62 57 7."
        else:
            arcz = ".1 13 34 45 36 63 57 7."
        self.check_coverage("""\
            a, i = 1, 0
            while 1:
                if i >= 3:
                    a = 4
                    break
                i += 1
            assert a == 4 and i == 3
            """,
            arcz=arcz,
        )

    def test_while_true(self) -> None:
        # With "while True", 2.x thinks it's computation,
        # 3.x thinks it's constant.
        if env.PYBEHAVIOR.keep_constant_test:
            arcz = ".1 12 23 34 45 36 62 57 7."
        else:
            arcz = ".1 13 34 45 36 63 57 7."
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

    def test_zero_coverage_while_loop(self) -> None:
        # https://github.com/nedbat/coveragepy/issues/502
        self.make_file("main.py", "print('done')")
        self.make_file("zero.py", """\
            def method(self):
                while True:
                    return 1
            """)
        cov = coverage.Coverage(source=["."], branch=True)
        self.start_import_stop(cov, "main")
        assert self.stdout() == 'done\n'
        if env.PYBEHAVIOR.keep_constant_test:
            num_stmts = 3
        else:
            num_stmts = 2
        expected = f"zero.py {num_stmts} {num_stmts} 0 0 0% 1-3"
        report = self.get_report(cov, show_missing=True)
        squeezed = self.squeezed_lines(report)
        assert expected in squeezed[3]

    def test_bug_496_continue_in_constant_while(self) -> None:
        # https://github.com/nedbat/coveragepy/issues/496
        # A continue in a while-true needs to jump to the right place.
        if env.PYBEHAVIOR.keep_constant_test:
            arcz = ".1 12 23 34 45 52 46 67 7."
        else:
            arcz = ".1 13 34 45 53 46 67 7."
        self.check_coverage("""\
            up = iter('ta')
            while True:
                char = next(up)
                if char == 't':
                    continue
                i = "line 6"
                break
            """,
            arcz=arcz,
        )

    def test_for_if_else_for(self) -> None:
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
                ".1 18 8G GH H. " +
                ".2 23 34 43 26 3. 6. " +
                "-89 9A 9-8 AB BC CB B9 AE E9",
            arcz_missing="26 6.",
        )

    def test_for_else(self) -> None:
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
            arcz=".1 .2 23 32 34 47 26 67 7. 18 89 9.",
        )

    def test_while_else(self) -> None:
        self.check_coverage("""\
            def whileelse(seq):
                while seq:
                    n = seq.pop()
                    if n > 4:
                        break
                else:
                    n = 99
                return n
            assert whileelse([1, 2]) == 99
            assert whileelse([1, 5]) == 5
            """,
            arcz=".1 19 9A A.  .2 23 34 45 58 42 27 78 8.",
        )

    def test_confusing_for_loop_bug_175(self) -> None:
        if env.PYBEHAVIOR.comprehensions_are_functions:
            extra_arcz = " -22 2-2"
        else:
            extra_arcz = ""
        self.check_coverage("""\
            o = [(1,2), (3,4)]
            o = [a for a in o]
            for tup in o:
                x = tup[0]
                y = tup[1]
            """,
            arcz=".1 12 23 34 45 53 3." + extra_arcz,
        )
        self.check_coverage("""\
            o = [(1,2), (3,4)]
            for tup in [a for a in o]:
                x = tup[0]
                y = tup[1]
            """,
            arcz=".1 12 23 34 42 2." + extra_arcz,
        )

    # https://bugs.python.org/issue44672
    @pytest.mark.xfail(env.PYVERSION < (3, 10), reason="<3.10 traced final pass incorrectly")
    def test_incorrect_loop_exit_bug_1175(self) -> None:
        self.check_coverage("""\
            def wrong_loop(x):
                if x:
                    for i in [3, 33]:
                        print(i+4)
                else:
                    pass

            wrong_loop(8)
            """,
            arcz=".1 .2 23 26 34 43 3. 6. 18 8.",
            arcz_missing="26 6.",
        )

    # https://bugs.python.org/issue44672
    @pytest.mark.xfail(env.PYVERSION < (3, 10), reason="<3.10 traced final pass incorrectly")
    def test_incorrect_if_bug_1175(self) -> None:
        self.check_coverage("""\
            def wrong_loop(x):
                if x:
                    if x:
                        print(4)
                else:
                    pass

            wrong_loop(8)
            """,
            arcz=".1 .2 23 26 34 4. 3. 6. 18 8.",
            arcz_missing="26 3. 6.",
        )

    def test_generator_expression(self) -> None:
        # Generator expression:
        self.check_coverage("""\
            o = ((1,2), (3,4))
            o = (a for a in o)
            for tup in o:
                x = tup[0]
                y = tup[1]
            """,
            arcz=".1 -22 2-2 12 23 34 45 53 3.",
        )

    def test_generator_expression_another_way(self) -> None:
        # https://bugs.python.org/issue44450
        # Generator expression:
        self.check_coverage("""\
            o = ((1,2), (3,4))
            o = (a for
                 a in
                 o)
            for tup in o:
                x = tup[0]
                y = tup[1]
            """,
            arcz=".1 -22 2-2 12 25 56 67 75 5.",
        )

    def test_other_comprehensions(self) -> None:
        if env.PYBEHAVIOR.comprehensions_are_functions:
            extra_arcz = " -22 2-2"
        else:
            extra_arcz = ""
        # Set comprehension:
        self.check_coverage("""\
            o = ((1,2), (3,4))
            o = {a for a in o}
            for tup in o:
                x = tup[0]
                y = tup[1]
            """,
            arcz=".1 12 23 34 45 53 3." + extra_arcz,
        )
        # Dict comprehension:
        self.check_coverage("""\
            o = ((1,2), (3,4))
            o = {a:1 for a in o}
            for tup in o:
                x = tup[0]
                y = tup[1]
            """,
            arcz=".1 12 23 34 45 53 3." + extra_arcz,
        )

    def test_multiline_dict_comp(self) -> None:
        if env.PYBEHAVIOR.comprehensions_are_functions:
            extra_arcz = " 2-2"
        else:
            extra_arcz = ""
        # Multiline dict comp:
        self.check_coverage("""\
            # comment
            d = \\
                {
                i:
                    str(i)
                for
                    i
                    in
                    range(9)
            }
            x = 11
            """,
            arcz="-22 2B B-2" + extra_arcz,
        )
        # Multi dict comp:
        self.check_coverage("""\
            # comment
            d = \\
                {
                (i, j):
                    str(i+j)
                for
                    i
                    in
                    range(9)
                for
                    j
                    in
                    range(13)
            }
            x = 15
            """,
            arcz="-22 2F F-2" + extra_arcz,
        )


class ExceptionArcTest(CoverageTest):
    """Arc-measuring tests involving exception handling."""

    def test_try_except(self) -> None:
        self.check_coverage("""\
            a, b = 1, 1
            try:
                a = 3
            except:
                b = 5
            assert a == 3 and b == 1
            """,
            arcz=".1 12 23 36 45 56 6.", arcz_missing="45 56",
        )

    def test_raise_followed_by_statement(self) -> None:
        if env.PYBEHAVIOR.omit_after_jump:
            arcz = ".1 12 23 34 46 67 78 8."
            arcz_missing = ""
        else:
            arcz = ".1 12 23 34 46 58 67 78 8."
            arcz_missing = "58"
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
            arcz=arcz, arcz_missing=arcz_missing,
        )

    def test_hidden_raise(self) -> None:
        self.check_coverage("""\
            a, b = 1, 1
            def oops(x):
                if x % 2:
                    raise Exception("odd")
            try:
                a = 6
                oops(1)
                a = 8
            except:
                b = 10
            assert a == 6 and b == 10
            """,
            arcz=".1 12 -23 34 3-2 4-2 25 56 67 78 8B 9A AB B.",
            arcz_missing="3-2 78 8B", arcz_unpredicted="79",
        )

    def test_except_with_type(self) -> None:
        self.check_coverage("""\
            a, b = 1, 1
            def oops(x):
                if x % 2:
                    raise ValueError("odd")
            def try_it(x):
                try:
                    a = 7
                    oops(x)
                    a = 9
                except ValueError:
                    b = 11
                return a
            assert try_it(0) == 9   # C
            assert try_it(1) == 7   # D
            """,
            arcz=".1 12 -23 34 3-2 4-2 25 5D DE E. -56 67 78 89 9C AB BC C-5",
            arcz_unpredicted="8A",
        )

    @xfail_pypy_3882
    def test_try_finally(self) -> None:
        self.check_coverage("""\
            a, c = 1, 1
            try:
                a = 3
            finally:
                c = 5
            assert a == 3 and c == 5
            """,
            arcz=".1 12 23 35 56 6.",
        )
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
            arcz=".1 12 23 34 46 78 89 69 9.",
            arcz_missing="78 89",
        )
        self.check_coverage("""\
            a, c, d = 1, 1, 1
            try:
                try:
                    a = 4
                    raise Exception("Yikes!")
                    # line 6
                finally:
                    c = 8
            except:
                d = 10                              # A
            assert a == 4 and c == 8 and d == 10    # B
            """,
            arcz=".1 12 23 34 45 58 89 9A AB B.",
            arcz_missing="",
        )

    @xfail_pypy_3882
    def test_finally_in_loop(self) -> None:
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
            arcz=".1 12 23 34 3D 45 56 67 68 7A 8A A3 AB BC CD D.",
            arcz_missing="3D",
        )
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
            arcz=".1 12 23 34 3D 45 56 67 68 7A 8A A3 AB BC CD D.",
            arcz_missing="67 7A AB BC CD",
        )


    @xfail_pypy_3882
    def test_break_through_finally(self) -> None:
        arcz = ".1 12 23 34 3D 45 56 67 68 7A    AD 8A A3 BC CD D."
        if env.PYBEHAVIOR.finally_jumps_back:
            arcz = arcz.replace("AD", "A7 7D")
        self.check_coverage("""\
            a, c, d, i = 1, 1, 1, 99
            try:
                for i in range(3):
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
            arcz=arcz,
            arcz_missing="3D BC CD",
        )

    def test_break_continue_without_finally(self) -> None:
        self.check_coverage("""\
            a, c, d, i = 1, 1, 1, 99
            try:
                for i in range(3):
                    try:
                        a = 5
                        if i > 0:
                            break
                        continue
                    except:
                        c = 10
            except:
                d = 12                              # C
            assert a == 5 and c == 1 and d == 1     # D
            """,
            arcz=".1 12 23 34 3D 45 56 67 68 7D 83 9A A3 BC CD D.",
            arcz_missing="3D 9A A3 BC CD",
        )

    @xfail_pypy_3882
    def test_continue_through_finally(self) -> None:
        arcz = ".1 12 23 34 3D 45 56 67 68       7A 8A A3 BC CD D."
        if env.PYBEHAVIOR.finally_jumps_back:
            arcz += " 73 A7"
        self.check_coverage("""\
            a, b, c, d, i = 1, 1, 1, 1, 99
            try:
                for i in range(3):
                    try:
                        a = 5
                        if i > 0:
                            continue
                        b = 8
                    finally:
                        c = 10
            except:
                d = 12                              # C
            assert (a, b, c, d) == (5, 8, 10, 1)    # D
            """,
            arcz=arcz,
            arcz_missing="BC CD",
        )

    def test_finally_in_loop_bug_92(self) -> None:
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
        )

    def test_bug_212(self) -> None:
        # "except Exception as e" is crucial here.
        # Bug 212 said that the "if exc" line was incorrectly marked as only
        # partially covered.
        self.check_coverage("""\
            def b(exc):
                try:
                    while "no peephole".upper():
                        raise Exception(exc)    # 4
                except Exception as e:
                    if exc != 'expected':
                        raise
                    q = 8

            b('expected')
            try:
                b('unexpected')     # C
            except:
                pass
            """,
            arcz=".1 .2 1A 23 34 3. 45 56 67 68 7. 8. AB BC C. DE E.",
            arcz_missing="3. C.",
            arcz_unpredicted="CD",
        )

    def test_except_finally(self) -> None:
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
            arcz=".1 12 23 45 37 57 78 8.", arcz_missing="45 57",
        )
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
            arcz=".1 12 -23 3-2 24 45 56 67 7B 89 9B BC C.",
            arcz_missing="67 7B", arcz_unpredicted="68",
        )

    def test_multiple_except_clauses(self) -> None:
        self.check_coverage("""\
            a, b, c = 1, 1, 1
            try:
                a = 3
            except ValueError:
                b = 5
            except IndexError:
                a = 7
            finally:
                c = 9
            assert a == 3 and b == 1 and c == 9
            """,
            arcz=".1 12 23 45 46 39 59 67 79 9A A.",
            arcz_missing="45 59 46 67 79",
        )
        self.check_coverage("""\
            a, b, c = 1, 1, 1
            try:
                a = int("xyz")  # ValueError
            except ValueError:
                b = 5
            except IndexError:
                a = 7
            finally:
                c = 9
            assert a == 1 and b == 5 and c == 9
            """,
            arcz=".1 12 23 45 46 39 59 67 79 9A A.",
            arcz_missing="39 46 67 79",
            arcz_unpredicted="34",
        )
        self.check_coverage("""\
            a, b, c = 1, 1, 1
            try:
                a = [1][3]      # IndexError
            except ValueError:
                b = 5
            except IndexError:
                a = 7
            finally:
                c = 9
            assert a == 7 and b == 1 and c == 9
            """,
            arcz=".1 12 23 45 46 39 59 67 79 9A A.",
            arcz_missing="39 45 59",
            arcz_unpredicted="34",
        )
        self.check_coverage("""\
            a, b, c = 1, 1, 1
            try:
                try:
                    a = 4/0         # ZeroDivisionError
                except ValueError:
                    b = 6
                except IndexError:
                    a = 8
                finally:
                    c = 10
            except ZeroDivisionError:
                pass
            assert a == 1 and b == 1 and c == 10
            """,
            arcz=".1 12 23 34 4A 56 6A 57 78 8A AD BC CD D.",
            arcz_missing="4A 56 6A 78 8A AD",
            arcz_unpredicted="45 7A AB",
        )

    def test_return_finally(self) -> None:
        arcz = ".1 12 29 9A AB BC C-1   -23 34 45  7-2   57 38 8-2"
        if env.PYBEHAVIOR.finally_jumps_back:
            arcz = arcz.replace("7-2", "75 5-2")
        self.check_coverage("""\
            a = [1]
            def check_token(data):
                if data:
                    try:
                        return 5
                    finally:
                        a.append(7)
                return 8
            assert check_token(False) == 8
            assert a == [1]
            assert check_token(True) == 5
            assert a == [1, 7]
            """,
            arcz=arcz,
        )

    @xfail_pypy_3882
    def test_except_jump_finally(self) -> None:
        arcz = (
            ".1 1Q QR RS ST TU U. " +
            ".2 23 34 45 56 4O 6L " +
            "78 89 9A AL   8B BC CD DL   BE EF FG GL   EH HI IJ JL  HL " +
            "LO L4 L. LM " +
            "MN NO O."
        )
        if env.PYBEHAVIOR.finally_jumps_back:
            arcz = arcz.replace("LO", "LA AO").replace("L4", "L4 LD D4").replace("L.", "LG G.")
        self.check_coverage("""\
            def func(x):
                a = f = g = 2
                try:
                    for i in range(4):
                        try:
                            6/0
                        except ZeroDivisionError:
                            if x == 'break':
                                a = 9
                                break
                            elif x == 'continue':
                                a = 12
                                continue
                            elif x == 'return':
                                a = 15                      # F
                                return a, f, g, i           # G
                            elif x == 'raise':              # H
                                a = 18                      # I
                                raise ValueError()          # J
                        finally:
                            f = 21                          # L
                except ValueError:                          # M
                    g = 23                                  # N
                return a, f, g, i                           # O

            assert func('break') == (9, 21, 2, 0)           # Q
            assert func('continue') == (12, 21, 2, 3)       # R
            assert func('return') == (15, 2, 2, 0)          # S
            assert func('raise') == (18, 21, 23, 0)         # T
            assert func('other') == (2, 21, 2, 3)           # U 30
            """,
            arcz=arcz,
            arcz_missing="6L",
            arcz_unpredicted="67",
        )

    @xfail_pypy_3882
    def test_else_jump_finally(self) -> None:
        arcz = (
            ".1 1S ST TU UV VW W. " +
            ".2 23 34 45 56 6A 78 8N 4Q " +
            "AB BC CN  AD DE EF FN  DG GH HI IN  GJ JK KL LN  JN " +
            "N4 NQ N. NO " +
            "OP PQ Q."
        )
        if env.PYBEHAVIOR.finally_jumps_back:
            arcz = arcz.replace("NQ", "NC CQ").replace("N4", "N4 NF F4").replace("N.", "NI I.")
        self.check_coverage("""\
            def func(x):
                a = f = g = 2
                try:
                    for i in range(4):
                        try:
                            b = 6
                        except ZeroDivisionError:
                            pass
                        else:
                            if x == 'break':
                                a = 11
                                break
                            elif x == 'continue':
                                a = 14
                                continue
                            elif x == 'return':
                                a = 17                      # H
                                return a, f, g, i           # I
                            elif x == 'raise':              # J
                                a = 20                      # K
                                raise ValueError()          # L
                        finally:
                            f = 23                          # N
                except ValueError:                          # O
                    g = 25                                  # P
                return a, f, g, i                           # Q

            assert func('break') == (11, 23, 2, 0)          # S
            assert func('continue') == (14, 23, 2, 3)       # T
            assert func('return') == (17, 2, 2, 0)          # U
            assert func('raise') == (20, 23, 25, 0)         # V
            assert func('other') == (2, 23, 2, 3)           # W 32
            """,
            arcz=arcz,
            arcz_missing="78 8N",
            arcz_unpredicted="",
        )


class YieldTest(CoverageTest):
    """Arc tests for generators."""

    def test_yield_in_loop(self) -> None:
        self.check_coverage("""\
            def gen(inp):
                for n in inp:
                    yield n

            list(gen([1,2,3]))
            """,
            arcz=".1 .2 23 2. 32 15 5.",
        )

    def test_padded_yield_in_loop(self) -> None:
        self.check_coverage("""\
            def gen(inp):
                i = 2
                for n in inp:
                    i = 4
                    yield n
                    i = 6
                i = 7

            list(gen([1,2,3]))
            """,
            arcz=".1 19 9.  .2 23 34 45 56 63 37 7.",
        )

    def test_bug_308(self) -> None:
        self.check_coverage("""\
            def run():
                for i in range(10):
                    yield lambda: i

            for f in run():
                print(f())
            """,
            arcz=".1 15 56 65 5.  .2 23 32 2.  -33 3-3",
        )
        self.check_coverage("""\
            def run():
                yield lambda: 100
                for i in range(10):
                    yield lambda: i

            for f in run():
                print(f())
            """,
            arcz=".1 16 67 76 6.  .2 23 34 43 3.   -22 2-2  -44 4-4",
        )
        self.check_coverage("""\
            def run():
                yield lambda: 100  # no branch miss

            for f in run():
                print(f())
            """,
            arcz=".1 14 45 54 4.  .2 2.  -22 2-2",
        )

    def test_bug_324(self) -> None:
        # This code is tricky: the list() call pulls all the values from gen(),
        # but each of them is a generator itself that is never iterated.  As a
        # result, the generator expression on line 3 is never entered or run.
        self.check_coverage("""\
            def gen(inp):
                for n in inp:
                    yield (i * 2 for i in range(n))

            list(gen([1,2,3]))
            """,
            arcz=
                ".1 15 5. "     # The module level
                ".2 23 32 2. "  # The gen() function
                "-33 3-3",      # The generator expression
            arcz_missing="-33 3-3",
        )

    def test_coroutines(self) -> None:
        self.check_coverage("""\
            def double_inputs():
                while len([1]):     # avoid compiler differences
                    x = yield
                    x *= 2
                    yield x

            gen = double_inputs()
            next(gen)
            print(gen.send(10))
            next(gen)
            print(gen.send(6))
            """,
            arcz=".1 17 78 89 9A AB B. .2 23 34 45 52 2.",
            arcz_missing="2.",
        )
        assert self.stdout() == "20\n12\n"

    def test_yield_from(self) -> None:
        self.check_coverage("""\
            def gen(inp):
                i = 2
                for n in inp:
                    i = 4
                    yield from range(3)
                    i = 6
                i = 7

            list(gen([1,2,3]))
            """,
            arcz=".1 19 9.  .2 23 34 45 56 63 37 7.",
        )

    def test_abandoned_yield(self) -> None:
        # https://github.com/nedbat/coveragepy/issues/440
        self.check_coverage("""\
            def gen():
                print(2)
                yield 3
                print(4)

            print(next(gen()))
            """,
            lines=[1, 2, 3, 4, 6],
            missing="4",
            arcz=".1 16 6.  .2 23 34 4.",
            arcz_missing="34 4.",
        )
        assert self.stdout() == "2\n3\n"


@pytest.mark.skipif(not env.PYBEHAVIOR.match_case, reason="Match-case is new in 3.10")
class MatchCaseTest(CoverageTest):
    """Tests of match-case."""
    def test_match_case_with_default(self) -> None:
        self.check_coverage("""\
            for command in ["huh", "go home", "go n"]:
                match command.split():
                    case ["go", direction] if direction in "nesw":
                        match = f"go: {direction}"
                    case ["go", _]:
                        match = "no go"
                    case _:
                        match = "default"
                print(match)
            """,
            arcz=".1 12 23 34 49 35 56 69 57 78 89 91 1.",
        )
        assert self.stdout() == "default\nno go\ngo: n\n"

    def test_match_case_with_wildcard(self) -> None:
        self.check_coverage("""\
            for command in ["huh", "go home", "go n"]:
                match command.split():
                    case ["go", direction] if direction in "nesw":
                        match = f"go: {direction}"
                    case ["go", _]:
                        match = "no go"
                    case x:
                        match = f"default: {x}"
                print(match)
            """,
            arcz=".1 12 23 34 49 35 56 69 57 78 89 91 1.",
        )
        assert self.stdout() == "default: ['huh']\nno go\ngo: n\n"

    def test_match_case_without_wildcard(self) -> None:
        self.check_coverage("""\
            match = None
            for command in ["huh", "go home", "go n"]:
                match command.split():
                    case ["go", direction] if direction in "nesw":
                        match = f"go: {direction}"
                    case ["go", _]:
                        match = "no go"
                print(match)
            """,
            arcz=".1 12 23 34 45 58 46 78 67 68 82 2.",
        )
        assert self.stdout() == "None\nno go\ngo: n\n"

    def test_absurd_wildcards(self) -> None:
        # https://github.com/nedbat/coveragepy/issues/1421
        self.check_coverage("""\
            def absurd(x):
                match x:
                    case (3 | 99 | (999 | _)):
                        print("default")
            absurd(5)
            """,
            # No arc from 3 to 5 because 3 always matches.
            arcz=".1 15 5.  .2 23 34 4.",
        )
        assert self.stdout() == "default\n"
        self.check_coverage("""\
            def absurd(x):
                match x:
                    case (3 | 99 | 999 as y):
                        print("not default")
            absurd(5)
            """,
            arcz=".1 15 5.  .2 23 34 3. 4.",
            arcz_missing="34 4.",
        )
        assert self.stdout() == ""
        self.check_coverage("""\
            def absurd(x):
                match x:
                    case (3 | 17 as y):
                        print("not default")
                    case 7: # 5
                        print("also not default")
            absurd(7)
            """,
            arcz=".1 17 7.  .2 23 34 4. 35 56 5. 6.",
            arcz_missing="34 4. 5.",
        )
        assert self.stdout() == "also not default\n"
        self.check_coverage("""\
            def absurd(x):
                match x:
                    case 3:
                        print("not default")
                    case _ if x == 7: # 5
                        print("also not default")
            absurd(7)
            """,
            arcz=".1 17 7.  .2 23 34 4. 35 56 5. 6.",
            arcz_missing="34 4. 5.",
        )
        assert self.stdout() == "also not default\n"


class OptimizedIfTest(CoverageTest):
    """Tests of if statements being optimized away."""

    def test_optimized_away_if_0(self) -> None:
        if env.PYBEHAVIOR.keep_constant_test:
            lines = [1, 2, 3, 4, 8, 9]
            arcz = ".1 12 23 24 34 48 49 89 9."
            arcz_missing = "24"
            # 49 isn't missing because line 4 is matched by the default partial
            # exclusion regex, and no branches are considered missing if they
            # start from an excluded line.
        else:
            lines = [1, 2, 3, 8, 9]
            arcz = ".1 12 23 28 38 89 9."
            arcz_missing = "28"

        self.check_coverage("""\
            a = 1
            if len([2]):
                c = 3
            if 0:
                if len([5]):
                    d = 6
            else:
                e = 8
            f = 9
            """,
            lines=lines,
            arcz=arcz,
            arcz_missing=arcz_missing,
        )

    def test_optimized_away_if_1(self) -> None:
        if env.PYBEHAVIOR.keep_constant_test:
            lines = [1, 2, 3, 4, 5, 6, 9]
            arcz = ".1 12 23 24 34 45 49 56 69 59 9."
            arcz_missing = "24 59"
            # 49 isn't missing because line 4 is matched by the default partial
            # exclusion regex, and no branches are considered missing if they
            # start from an excluded line.
        else:
            lines = [1, 2, 3, 5, 6, 9]
            arcz = ".1 12 23 25 35 56 69 59 9."
            arcz_missing = "25 59"

        self.check_coverage("""\
            a = 1
            if len([2]):
                c = 3
            if 1:
                if len([5]):
                    d = 6
            else:
                e = 8
            f = 9
            """,
            lines=lines,
            arcz=arcz,
            arcz_missing=arcz_missing,
        )

    def test_optimized_away_if_1_no_else(self) -> None:
        if env.PYBEHAVIOR.keep_constant_test:
            lines = [1, 2, 3, 4, 5]
            arcz = ".1 12 23 25 34 45 5."
            arcz_missing = ""
            # 25 isn't missing because line 2 is matched by the default partial
            # exclusion regex, and no branches are considered missing if they
            # start from an excluded line.
        else:
            lines = [1, 3, 4, 5]
            arcz = ".1 13 34 45 5."
            arcz_missing = ""
        self.check_coverage("""\
            a = 1
            if 1:
                b = 3
                c = 4
            d = 5
            """,
            lines=lines,
            arcz=arcz,
            arcz_missing=arcz_missing,
        )

    def test_optimized_if_nested(self) -> None:
        if env.PYBEHAVIOR.keep_constant_test:
            lines = [1, 2, 8, 11, 12, 13, 14, 15]
            arcz = ".1 12 28 2F 8B 8F BC CD DE EF F."
            arcz_missing = ""
            # 2F and 8F aren't missing because they're matched by the default
            # partial exclusion regex, and no branches are considered missing
            # if they start from an excluded line.
        else:
            lines = [1, 12, 14, 15]
            arcz = ".1 1C CE EF F."
            arcz_missing = ""

        self.check_coverage("""\
            a = 1
            if 0:
                if 0:
                    b = 4
                else:
                    c = 6
            else:
                if 0:
                    d = 9
                else:
                    if 0: e = 11
                    f = 12
                    if 0: g = 13
                    h = 14
            i = 15
            """,
            lines=lines,
            arcz=arcz,
            arcz_missing=arcz_missing,
        )

    def test_dunder_debug(self) -> None:
        # Since some of our tests use __debug__, let's make sure it is true as
        # we expect
        assert __debug__
        # Check that executed code has __debug__
        self.check_coverage("""\
            assert __debug__, "assert __debug__"
            """,
        )
        # Check that if it didn't have debug, it would let us know.
        with pytest.raises(AssertionError):
            self.check_coverage("""\
                assert not __debug__, "assert not __debug__"
                """,
            )

    def test_if_debug(self) -> None:
        if env.PYBEHAVIOR.optimize_if_debug:
            arcz = ".1 12 24 41 26 61 1."
            arcz_missing = ""
        else:
            arcz = ".1 12 23 31 34 41 26 61 1."
            arcz_missing = "31"
        self.check_coverage("""\
            for value in [True, False]:
                if value:
                    if __debug__:
                        x = 4
                else:
                    x = 6
            """,
            arcz=arcz,
            arcz_missing=arcz_missing,
        )

    @xfail_pypy_3882
    def test_if_not_debug(self) -> None:
        if env.PYBEHAVIOR.optimize_if_not_debug == 1:
            arcz = ".1 12 23 34 42 37 72 28 8."
        elif env.PYBEHAVIOR.optimize_if_not_debug == 2:
            arcz = ".1 12 23 35 52 37 72 28 8."
        else:
            assert env.PYBEHAVIOR.optimize_if_not_debug == 3
            arcz = ".1 12 23 32 37 72 28 8."

        self.check_coverage("""\
            lines = set()
            for value in [True, False]:
                if value:
                    if not __debug__:
                        lines.add(5)
                else:
                    lines.add(7)
            assert lines == set([7])
            """,
            arcz=arcz,
        )


class MiscArcTest(CoverageTest):
    """Miscellaneous arc-measuring tests."""

    def test_dict_literal(self) -> None:
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
            arcz=".1 19 9.",
        )
        self.check_coverage("""\
            d = \\
                { 'a': 2,
                'b': 3,
                'c': {
                    'd': 5,
                    'e': 6,
                    }
                }
            assert d
            """,
            arcz=".1 19 9.",
        )

    def test_unpacked_literals(self) -> None:
        self.check_coverage("""\
            d = {
                'a': 2,
                'b': 3,
            }
            weird = {
                **d,
                **{'c': 7},
                'd': 8,
            }
            assert weird['b'] == 3
            """,
            arcz=".1 15 5A A.",
        )
        self.check_coverage("""\
            l = [
                2,
                3,
            ]
            weird = [
                *l,
                *[7],
                8,
            ]
            assert weird[1] == 3
            """,
            arcz=".1 15 5A A.",
        )

    @pytest.mark.parametrize("n", [10, 50, 100, 500, 1000, 2000, 10000])
    def test_pathologically_long_code_object(self, n: int) -> None:
        # https://github.com/nedbat/coveragepy/issues/359
        # Long code objects sometimes cause problems. Originally, it was
        # due to EXTENDED_ARG bytes codes.  Then it showed a mistake in
        # line-number packing.
        code = """\
            data = [
            """ + "".join(f"""\
                [
                    {i}, {i}, {i}, {i}, {i}, {i}, {i}, {i}, {i}, {i}],
            """ for i in range(n)
            ) + """\
            ]

            print(len(data))
            """
        self.check_coverage(code, arcs=[(-1, 1), (1, 2*n+4), (2*n+4, -1)])
        assert self.stdout() == f"{n}\n"

    def test_partial_generators(self) -> None:
        # https://github.com/nedbat/coveragepy/issues/475
        # Line 2 is executed completely.
        # Line 3 is started but not finished, because zip ends before it finishes.
        # Line 4 is never started.
        cov = self.check_coverage("""\
            def f(a, b):
                c = (i for i in a)          # 2
                d = (j for j in b)          # 3
                e = (k for k in b)          # 4
                return dict(zip(c, d))

            f(['a', 'b'], [1, 2, 3])
            """,
            arcz=".1 17 7.  .2 23 34 45 5.  -22 2-2  -33 3-3  -44 4-4",
            arcz_missing="3-3 -44 4-4",
        )
        expected = "line 3 didn't finish the generator expression on line 3"
        assert self.get_missing_arc_description(cov, 3, -3) == expected
        expected = "line 4 didn't run the generator expression on line 4"
        assert self.get_missing_arc_description(cov, 4, -4) == expected


class DecoratorArcTest(CoverageTest):
    """Tests of arcs with decorators."""

    def test_function_decorator(self) -> None:
        arcz = (
            ".1 16 67 7A AE EF F. "     # main line
            ".2 24 4.   -23 3-2 "       # decorators
            "-6D D-6 "                  # my_function
        )
        if env.PYBEHAVIOR.trace_decorator_line_again:
            arcz += "A7 76 6A "
        self.check_coverage("""\
            def decorator(arg):
                def _dec(f):
                    return f
                return _dec

            @decorator(6)
            @decorator(
                len([8]),
            )
            def my_function(
                a=len([11]),
            ):
                x = 13
            a = 14
            my_function()
            """,
            arcz=arcz,
        )

    @xfail_pypy38
    def test_class_decorator(self) -> None:
        arcz = (
            ".1 16 67 6D 7A AE E. "     # main line
            ".2 24 4.   -23 3-2 "       # decorators
            "-66 D-6 "                  # MyObject
        )
        if env.PYBEHAVIOR.trace_decorator_line_again:
            arcz += "A7 76 6A "
        self.check_coverage("""\
            def decorator(arg):
                def _dec(c):
                    return c
                return _dec

            @decorator(6)
            @decorator(
                len([8]),
            )
            class MyObject(
                object
            ):
                X = 13
            a = 14
            """,
            arcz=arcz,
        )

    def test_bug_466a(self) -> None:
        # A bad interaction between decorators and multi-line list assignments,
        # believe it or not...!
        arcz = ".1 1A A.  13 34 4.  -35 58 8-3 "
        if env.PYBEHAVIOR.trace_decorator_line_again:
            arcz += "43 "
        # This example makes more sense when considered in tandem with 466b below.
        self.check_coverage("""\
            class Parser(object):

                @classmethod
                def parse(cls):
                    formats = [ 5 ]


                    return None

            Parser.parse()
            """,
            arcz=arcz,
        )

    def test_bug_466b(self) -> None:
        # A bad interaction between decorators and multi-line list assignments,
        # believe it or not...!
        arcz = ".1 1A A.  13 34 4.  -35 58 8-3 "
        if env.PYBEHAVIOR.trace_decorator_line_again:
            arcz += "43 "
        self.check_coverage("""\
            class Parser(object):

                @classmethod
                def parse(cls):
                    formats = [
                        6,
                    ]
                    return None

            Parser.parse()
            """,
            arcz=arcz,
        )


class LambdaArcTest(CoverageTest):
    """Tests of lambdas"""

    def test_multiline_lambda(self) -> None:
        self.check_coverage("""\
            fn = (lambda x:
                    x + 2
            )
            assert fn(4) == 6
            """,
            arcz=".1 14 4-1   1-1",
        )
        self.check_coverage("""\

            fn = \\
                (
                lambda
                    x:
                    x
                    +
                    8
            )
            assert fn(10) == 18
            """,
            arcz="-22 2A A-2   2-2",
        )

    def test_unused_lambdas_are_confusing_bug_90(self) -> None:
        self.check_coverage("""\
            a = 1
            fn = lambda x: x
            b = 3
            """,
            arcz=".1 12 -22 2-2 23 3.", arcz_missing="-22 2-2",
        )

    def test_raise_with_lambda_looks_like_partial_branch(self) -> None:
        self.check_coverage("""\
            def ouch(fn):
                2/0
            a = b = c = d = 3
            try:
                a = ouch(lambda: 5)
                if a:
                    b = 7
            except ZeroDivisionError:
                c = 9
            d = 10
            assert (a, b, c, d) == (3, 3, 9, 10)
            """,
            lines=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            missing="6-7",
            arcz=".1 13 34 45 56 67 6A 7A 89 9A AB B.   .2 2.  -55 5-5",
            arcz_missing="56 67 6A 7A  -55 5-5",
            arcz_unpredicted="58",
        )

    def test_lambda_in_dict(self) -> None:
        self.check_coverage("""\
            x = 1
            x = 2
            d = {
                4: lambda: [],
                5: lambda: [],
                6: lambda: [],
                7: lambda: [],
            }

            for k, v in d.items():          # 10
                if k & 1:
                    v()
            """,
            arcz=".1 12 23 3A AB BC BA CA A.  -33  3-3",
        )


# This had been a failure on Mac 3.9, but it started passing on GitHub
# actions (running macOS 12) but still failed on my laptop (macOS 14).
# I don't understand why it failed, I don't understand why it passed,
# so just skip the whole thing.
skip_eventlet_670 = pytest.mark.skipif(
    env.PYVERSION[:2] == (3, 9) and env.CPYTHON and env.OSX,
    reason="Avoid an eventlet bug on Mac 3.9: eventlet#670",
    # https://github.com/eventlet/eventlet/issues/670
)


class AsyncTest(CoverageTest):
    """Tests of the new async and await keywords in Python 3.5"""

    @skip_eventlet_670
    def test_async(self) -> None:
        self.check_coverage("""\
            import asyncio

            async def compute(x, y):                        # 3
                print(f"Compute {x} + {y} ...")
                await asyncio.sleep(0.001)
                return x + y                                # 6

            async def print_sum(x, y):                      # 8
                result = (0 +
                            await compute(x, y)             # A
                )
                print(f"{x} + {y} = {result}")

            loop = asyncio.new_event_loop()                 # E
            loop.run_until_complete(print_sum(1, 2))
            loop.close()                                    # G
            """,
            arcz=
                ".1 13 38 8E EF FG G. " +
                "-34 45 56 6-3 " +
                "-89 9C C-8",
        )
        assert self.stdout() == "Compute 1 + 2 ...\n1 + 2 = 3\n"

    @skip_eventlet_670
    def test_async_for(self) -> None:
        self.check_coverage("""\
            import asyncio

            class AsyncIteratorWrapper:                 # 3
                def __init__(self, obj):                # 4
                    self._it = iter(obj)

                def __aiter__(self):                    # 7
                    return self

                async def __anext__(self):              # A
                    try:
                        return next(self._it)
                    except StopIteration:
                        raise StopAsyncIteration

            async def doit():                           # G
                async for letter in AsyncIteratorWrapper("abc"):
                    print(letter)
                print(".")

            loop = asyncio.new_event_loop()             # L
            loop.run_until_complete(doit())
            loop.close()
            """,
            arcz=
                ".1 13 3G GL LM MN N. "     # module main line
                "-33 34 47 7A A-3 "         # class definition
                "-GH HI IH HJ J-G "         # doit
                "-45 5-4 "                  # __init__
                "-78 8-7 "                  # __aiter__
                "-AB BC C-A DE E-A ",       # __anext__
            arcz_unpredicted="CD",
        )
        assert self.stdout() == "a\nb\nc\n.\n"

    def test_async_with(self) -> None:
        if env.PYBEHAVIOR.exit_through_with:
            arcz = ".1 1. .2 23 32 2."
            arcz_missing = ".2 23 32 2."
        else:
            arcz = ".1 1. .2 23 3."
            arcz_missing = ".2 23 3."
        self.check_coverage("""\
            async def go():
                async with x:
                    pass
            """,
            arcz=arcz,
            arcz_missing=arcz_missing,
        )

    def test_async_decorator(self) -> None:
        arcz = ".1 14 45 5.  .2 2.  -46 6-4 "
        if env.PYBEHAVIOR.trace_decorator_line_again:
            arcz += "54 "
        self.check_coverage("""\
            def wrap(f):        # 1
                return f

            @wrap               # 4
            async def go():
                return
            """,
            arcz=arcz,
            arcz_missing='-46 6-4',
        )

    # https://github.com/nedbat/coveragepy/issues/1158
    # https://bugs.python.org/issue44621
    @pytest.mark.skipif(env.PYVERSION[:2] == (3, 9), reason="avoid a 3.9 bug: 44621")
    def test_bug_1158(self) -> None:
        self.check_coverage("""\
            import asyncio

            async def async_gen():
                yield 4

            async def async_test():
                global a
                a = 8
                async for i in async_gen():
                    print(i + 10)
                else:
                    a = 12

            asyncio.run(async_test())
            assert a == 12
            """,
            arcz=".1 13 36 6E EF F.  -34 4-3  -68 89 9A 9C A9 C-6",
        )
        assert self.stdout() == "14\n"

    # https://github.com/nedbat/coveragepy/issues/1176
    # https://bugs.python.org/issue44622
    @skip_eventlet_670
    def test_bug_1176(self) -> None:
        self.check_coverage("""\
            import asyncio

            async def async_gen():
                yield 4

            async def async_test():
                async for i in async_gen():
                    print(i + 8)

            asyncio.run(async_test())
            """,
            arcz=".1 13 36 6A A.  -34 4-3  -67 78 87 7-6",
        )
        assert self.stdout() == "12\n"

    # https://github.com/nedbat/coveragepy/issues/1205
    def test_bug_1205(self) -> None:
        self.check_coverage("""\
            def func():
                if T(2):
                    if T(3):
                        if F(4):
                            if X(5):
                                return 6
                    else:
                        return 8
                elif X(9) and Y:
                    return 10

            T, F = (lambda _: True), (lambda _: False)
            func()
            """,
            arcz=".1 1C CD D.  .2 23 29 34 38 45 4. 56 5. 6. 8. 9. 9A A.  -CC C-C",
            arcz_missing="29 38 45 56 5. 6. 8. 9. 9A A.",
        )


class AnnotationTest(CoverageTest):
    """Tests using type annotations."""

    def test_annotations(self) -> None:
        self.check_coverage("""\
            def f(x:str, y:int) -> str:
                a:int = 2
                return f"{x}, {y}, {a}, 3"
            print(f("x", 4))
            """,
            arcz=".1 .2 23 3.  14 4.",
        )
        assert self.stdout() == "x, 4, 2, 3\n"


class ExcludeTest(CoverageTest):
    """Tests of exclusions to indicate known partial branches."""

    def test_default(self) -> None:
        # A number of forms of pragma comment are accepted.
        self.check_coverage("""\
            a = 1
            if a:   #pragma: no branch
                b = 3
            c = 4
            if c:   # pragma NOBRANCH
                d = 6
            e = 7
            if e:#\tpragma:\tno branch
                f = 9
            """,
            [1,2,3,4,5,6,7,8,9],
            arcz=".1 12 23 24 34 45 56 57 67 78 89 9. 8.",
        )

    def test_custom_pragmas(self) -> None:
        self.check_coverage("""\
            a = 1
            while a:    # [only some]
                c = 3
                break
            assert c == 5-2
            """,
            [1,2,3,4,5],
            partials=["only some"],
            arcz=".1 12 23 34 45 25 5.",
        )


class LineDataTest(CoverageTest):
    """Tests that line_data gives us what we expect."""

    def test_branch(self) -> None:
        cov = coverage.Coverage(branch=True)

        self.make_file("fun1.py", """\
            def fun1(x):
                if x == 1:
                    return

            fun1(3)
            """)

        self.start_import_stop(cov, "fun1")

        data = cov.get_data()
        fun1_lines = sorted_lines(data, abs_file("fun1.py"))
        assert_count_equal(fun1_lines, [1, 2, 5])
