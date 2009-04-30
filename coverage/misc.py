"""Miscellaneous stuff for Coverage."""

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


def format_lines(statements, lines):
    """Nicely format a list of line numbers.

    Format a list of line numbers for printing by coalescing groups of lines as
    long as the lines represent consecutive statements.  This will coalesce
    even if there are gaps between statements.
    
    For example, if `statements` is [1,2,3,4,5,10,11,12,13,14] and
    `lines` is [1,2,5,10,11,13,14] then the result will be "1-2, 5-11, 13-14".
    
    """
    pairs = []
    i = 0
    j = 0
    start = None
    pairs = []
    while i < len(statements) and j < len(lines):
        if statements[i] == lines[j]:
            if start == None:
                start = lines[j]
            end = lines[j]
            j = j + 1
        elif start:
            pairs.append((start, end))
            start = None
        i = i + 1
    if start:
        pairs.append((start, end))
    ret = ', '.join(map(nice_pair, pairs))
    return ret


class CoverageException(Exception):
    pass
