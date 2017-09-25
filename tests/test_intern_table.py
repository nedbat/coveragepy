from tests.coveragetest import CoverageTest

from hypothesis import given, example
import hypothesis.strategies as st
from coverage.tracer import InternTable
import sys


class TestInternTable(CoverageTest):
    @example([0])
    @given(st.lists(st.integers(0, 2 ** 64 - 1), unique=True))
    def test_interns_as_none_by_default(self, ls):
        table = InternTable()
        for i in ls:
            assert table[i] is None

    @example(list(range(23)))
    @example([0])
    @given(st.one_of(
        st.integers(0, 1000).map(lambda i: list(range(i))),
        st.lists(st.integers(0, 2 ** 64 - 1), unique=True),
    ))
    def test_can_intern_integers_as_themselves(self, ls):
        table = InternTable()
        for i in ls:
            table[i] = i
            assert table[i] is i
        for i in ls:
            assert table[i] == i
        assert len(table) == len(ls)

    @given(
        st.lists(st.tuples(st.integers(0, 2**64 - 1)), unique=True).map(
            lambda ls: list(map(list, ls))
        ),
    )
    def test_maintains_correct_ref_count(self, ls):
        def refs():
            return list(map(sys.getrefcount, ls))

        initial_refs = refs()
        assert refs() == initial_refs

        table = InternTable()

        for i in range(len(ls)):
            r = initial_refs[i]
            assert sys.getrefcount(ls[i]) == r + 1
            x = ls[i][0]
            table[x] = ls[i]
            assert sys.getrefcount(ls[i]) == r + 2
            table[x] = ls[i]
            assert sys.getrefcount(ls[i]) == r + 2

        del table
        assert refs() == initial_refs
