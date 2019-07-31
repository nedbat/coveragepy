# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Tests for coverage.numbits"""

from hypothesis import given
from hypothesis.strategies import sets, integers

from coverage.numbits import (
    nums_to_numbits, numbits_to_nums, merge_numbits, numbits_any_intersection,
    )

from tests.coveragetest import CoverageTest

# Hypothesis-generated line number data
line_numbers = sets(integers(min_value=1, max_value=9999), min_size=1)

class NumbitsOpTest(CoverageTest):
    """Tests of the numbits operations in numbits.py."""

    run_in_temp_dir = False

    @given(line_numbers)
    def test_conversion(self, nums):
        nums2 = numbits_to_nums(nums_to_numbits(nums))
        self.assertEqual(nums, set(nums2))

    @given(line_numbers, line_numbers)
    def test_merging(self, nums1, nums2):
        merged = numbits_to_nums(merge_numbits(nums_to_numbits(nums1), nums_to_numbits(nums2)))
        self.assertEqual(nums1 | nums2, set(merged))

    @given(line_numbers, line_numbers)
    def test_any_intersection(self, nums1, nums2):
        inter = numbits_any_intersection(nums_to_numbits(nums1), nums_to_numbits(nums2))
        expect = bool(nums1 & nums2)
        self.assertEqual(expect, bool(inter))
