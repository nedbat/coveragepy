# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Tests for coverage.numbits"""

from hypothesis import given, settings
from hypothesis.strategies import sets, integers

from coverage import env
from coverage.numbits import (
    nums_to_numbits, numbits_to_nums, merge_numbits, numbits_any_intersection,
    num_in_numbits,
    )

from tests.coveragetest import CoverageTest

# Hypothesis-generated line number data
line_numbers = integers(min_value=1, max_value=9999)
line_number_sets = sets(line_numbers, min_size=1)

# When coverage-testing ourselves, hypothesis complains about a test being
# flaky because the first run exceeds the deadline (and fails), and the second
# run succeeds.  Disable the deadline if we are coverage-testing.
default_settings = settings()
if env.METACOV:
    default_settings = settings(default_settings, deadline=None)


class NumbitsOpTest(CoverageTest):
    """Tests of the numbits operations in numbits.py."""

    run_in_temp_dir = False

    @given(line_number_sets)
    @settings(default_settings)
    def test_conversion(self, nums):
        nums2 = numbits_to_nums(nums_to_numbits(nums))
        self.assertEqual(nums, set(nums2))

    @given(line_number_sets, line_number_sets)
    @settings(default_settings)
    def test_merging(self, nums1, nums2):
        merged = numbits_to_nums(merge_numbits(nums_to_numbits(nums1), nums_to_numbits(nums2)))
        self.assertEqual(nums1 | nums2, set(merged))

    @given(line_number_sets, line_number_sets)
    @settings(default_settings)
    def test_any_intersection(self, nums1, nums2):
        inter = numbits_any_intersection(nums_to_numbits(nums1), nums_to_numbits(nums2))
        expect = bool(nums1 & nums2)
        self.assertEqual(expect, bool(inter))

    @given(line_numbers, line_number_sets)
    @settings(default_settings)
    def test_num_in_numbits(self, num, nums):
        numbits = nums_to_numbits(nums)
        is_in = num_in_numbits(num, numbits)
        self.assertEqual(num in nums, is_in)
