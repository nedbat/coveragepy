from tests.coveragetest import CoverageTest

from hypothesis import given, example
import hypothesis.strategies as st
from coverage.tracer import InternTable


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
