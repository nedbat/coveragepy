# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""
Functions to manipulate packed binary representations of number sets.

To save space, coverage stores sets of line numbers in SQLite using a packed
binary representation called a numbits.  A numbits is stored as a blob in the
database.  The exact meaning of the bytes in the blobs should be considered an
implementation detail that might change in the future.  Use these functions to
work with those binary blobs of data.

"""

from coverage.backward import bytes_to_ints, binary_bytes, zip_longest
from coverage.misc import contract


@contract(nums='Iterable', returns='bytes')
def nums_to_numbits(nums):
    """Convert `nums` (an iterable of ints) into a numbits."""
    nbytes = max(nums) // 8 + 1
    b = bytearray(nbytes)
    for num in nums:
        b[num//8] |= 1 << num % 8
    return bytes(b)

@contract(numbits='bytes', returns='list[int]')
def numbits_to_nums(numbits):
    """Convert a numbits into a list of numbers."""
    nums = []
    for byte_i, byte in enumerate(bytes_to_ints(numbits)):
        for bit_i in range(8):
            if (byte & (1 << bit_i)):
                nums.append(byte_i * 8 + bit_i)
    return nums

@contract(numbits1='bytes', numbits2='bytes', returns='bytes')
def merge_numbits(numbits1, numbits2):
    """Merge two numbits"""
    byte_pairs = zip_longest(bytes_to_ints(numbits1), bytes_to_ints(numbits2), fillvalue=0)
    return binary_bytes(b1 | b2 for b1, b2 in byte_pairs)
