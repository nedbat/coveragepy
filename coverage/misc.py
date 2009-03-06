"""Miscellaneous stuff for coverage.py"""

def nice_pair(pair):
    """Make a nice string representation of a pair of numbers.
    
    If the numbers are equal, just return the number, otherwise return the pair
    with a dash between them, indicating the range.
    
    """
    start, end = pair
    if start == end:
        return "%d" % start
    else:
        return "%d-%d" % (start, end)


class CoverageException(Exception):
    pass
