# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

"""Tests of miscellaneous stuff."""

import pytest

from coverage.misc import contract, dummy_decorator_with_args, file_be_gone
from coverage.misc import format_lines, Hasher, one_of

from tests.coveragetest import CoverageTest


class HasherTest(CoverageTest):
    """Test our wrapper of md5 hashing."""

    run_in_temp_dir = False

    def test_string_hashing(self):
        h1 = Hasher()
        h1.update("Hello, world!")
        h2 = Hasher()
        h2.update("Goodbye!")
        h3 = Hasher()
        h3.update("Hello, world!")
        self.assertNotEqual(h1.hexdigest(), h2.hexdigest())
        self.assertEqual(h1.hexdigest(), h3.hexdigest())

    def test_bytes_hashing(self):
        h1 = Hasher()
        h1.update(b"Hello, world!")
        h2 = Hasher()
        h2.update(b"Goodbye!")
        self.assertNotEqual(h1.hexdigest(), h2.hexdigest())

    def test_unicode_hashing(self):
        h1 = Hasher()
        h1.update(u"Hello, world! \N{SNOWMAN}")
        h2 = Hasher()
        h2.update(u"Goodbye!")
        self.assertNotEqual(h1.hexdigest(), h2.hexdigest())

    def test_dict_hashing(self):
        h1 = Hasher()
        h1.update({'a': 17, 'b': 23})
        h2 = Hasher()
        h2.update({'b': 23, 'a': 17})
        self.assertEqual(h1.hexdigest(), h2.hexdigest())


class RemoveFileTest(CoverageTest):
    """Tests of misc.file_be_gone."""

    def test_remove_nonexistent_file(self):
        # It's OK to try to remove a file that doesn't exist.
        file_be_gone("not_here.txt")

    def test_remove_actual_file(self):
        # It really does remove a file that does exist.
        self.make_file("here.txt", "We are here, we are here, we are here!")
        file_be_gone("here.txt")
        self.assert_doesnt_exist("here.txt")

    def test_actual_errors(self):
        # Errors can still happen.
        # ". is a directory" on Unix, or "Access denied" on Windows
        with self.assertRaises(OSError):
            file_be_gone(".")


class ContractTest(CoverageTest):
    """Tests of our contract decorators."""

    run_in_temp_dir = False

    def test_bytes(self):
        @contract(text='bytes|None')
        def need_bytes(text=None):                      # pylint: disable=missing-docstring
            return text

        assert need_bytes(b"Hey") == b"Hey"
        assert need_bytes() is None
        with pytest.raises(Exception):
            need_bytes(u"Oops")

    def test_unicode(self):
        @contract(text='unicode|None')
        def need_unicode(text=None):                    # pylint: disable=missing-docstring
            return text

        assert need_unicode(u"Hey") == u"Hey"
        assert need_unicode() is None
        with pytest.raises(Exception):
            need_unicode(b"Oops")

    def test_one_of(self):
        @one_of("a, b, c")
        def give_me_one(a=None, b=None, c=None):        # pylint: disable=missing-docstring
            return (a, b, c)

        assert give_me_one(a=17) == (17, None, None)
        assert give_me_one(b=set()) == (None, set(), None)
        assert give_me_one(c=17) == (None, None, 17)
        with pytest.raises(AssertionError):
            give_me_one(a=17, b=set())
        with pytest.raises(AssertionError):
            give_me_one()

    def test_dummy_decorator_with_args(self):
        @dummy_decorator_with_args("anything", this=17, that="is fine")
        def undecorated(a=None, b=None):                # pylint: disable=missing-docstring
            return (a, b)

        assert undecorated() == (None, None)
        assert undecorated(17) == (17, None)
        assert undecorated(b=23) == (None, 23)
        assert undecorated(b=42, a=3) == (3, 42)


@pytest.mark.parametrize("statements, lines, result", [
    (set([1,2,3,4,5,10,11,12,13,14]), set([1,2,5,10,11,13,14]), "1-2, 5-11, 13-14"),
    ([1,2,3,4,5,10,11,12,13,14,98,99], [1,2,5,10,11,13,14,99], "1-2, 5-11, 13-14, 99"),
    ([1,2,3,4,98,99,100,101,102,103,104], [1,2,99,102,103,104], "1-2, 99, 102-104"),
    ([17], [17], "17"),
    ([90,91,92,93,94,95], [90,91,92,93,94,95], "90-95"),
    ([1, 2, 3, 4, 5], [], ""),
    ([1, 2, 3, 4, 5], [4], "4"),
])
def test_format_lines(statements, lines, result):
    assert format_lines(statements, lines) == result
