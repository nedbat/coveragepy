# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Tests of coverage/instrument.py."""

from __future__ import annotations

import pytest

from coverage.instrument import is_branch, encode_branch, decode_branch

@pytest.mark.parametrize("from_lineno, to_lineno", [
    (1, 1),
    (9999, 17),
    (42, 9999),
])
def test_branch_encoding(from_lineno, to_lineno):
    lineno = encode_branch(from_lineno, to_lineno)
    assert is_branch(lineno)
    assert not is_branch(from_lineno)
    assert not is_branch(to_lineno)
    # The line number must fit in a C int.
    assert lineno < 2**31
    fl, tl = decode_branch(lineno)
    assert (fl, tl) == (from_lineno, to_lineno)
