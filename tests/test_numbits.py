# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Tests for coverage.numbits"""

import random

from coverage.numbits import nums_to_numbits, numbits_to_nums, merge_numbits

from tests.coveragetest import CoverageTest

class NumbitsOpTest(CoverageTest):
    """Tests of the numbits operations in numbits.py."""

    run_in_temp_dir = False

    def numbers(self, r):
        """Produce a list of numbers from a Random object."""
        return list(set(r.randint(1, 1000) for _ in range(r.randint(100, 200))))

    def test_conversion(self):
        r = random.Random(1792)
        for _ in range(10):
            nums = self.numbers(r)
            numbits = nums_to_numbits(nums)
            self.assertEqual(sorted(numbits_to_nums(numbits)), sorted(nums))

    def test_merging(self):
        r = random.Random(314159)
        for _ in range(10):
            nums1 = self.numbers(r)
            nums2 = self.numbers(r)
            merged = numbits_to_nums(merge_numbits(nums_to_numbits(nums1), nums_to_numbits(nums2)))
            all_nums = set()
            all_nums.update(nums1)
            all_nums.update(nums2)
            self.assertEqual(sorted(all_nums), sorted(merged))
