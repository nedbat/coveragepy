# Comment copied from Python/compile.c:
#
# All about a_lnotab.
# 
# c_lnotab is an array of unsigned bytes disguised as a Python string.
# It is used to map bytecode offsets to source code line #s (when needed
# for tracebacks).
# 
# The array is conceptually a list of
#     (bytecode offset increment, line number increment)
# pairs. The details are important and delicate, best illustrated by example:
# 
#     byte code offset   source code line number
#        0                   1
#        6                   2
#       50                   7
#      350                 307
#      361                 308
# 
# The first trick is that these numbers aren't stored, only the increments
# from one row to the next (this doesn't really work, but it's a start):
# 
#     0, 1,  6, 1,  44, 5,  300, 300,  11, 1
# 
# The second trick is that an unsigned byte can't hold negative values, or
# values larger than 255, so (a) there's a deep assumption that byte code
# offsets and their corresponding line #s both increase monotonically, and (b)
# if at least one column jumps by more than 255 from one row to the next, more
# than one pair is written to the table. In case #b, there's no way to know
# from looking at the table later how many were written.	That's the delicate
# part.  A user of c_lnotab desiring to find the source line number
# corresponding to a bytecode address A should do something like this
# 
#     lineno = addr = 0
#     for addr_incr, line_incr in c_lnotab:
#         addr += addr_incr
#         if addr > A:
#             return lineno
#         lineno += line_incr
# 
# In order for this to work, when the addr field increments by more than 255,
# the line # increment in each pair generated must be 0 until the remaining addr
# increment is < 256.  So, in the example above, assemble_lnotab (it used
# to be called com_set_lineno) should not (as was actually done until 2.2)
# expand 300, 300 to 255, 255, 45, 45, 
#             but to 255,   0, 45, 255, 0, 45.
# 

def lnotab(pairs, first_lineno=0):
    """Yields byte integers representing the pairs of integers passed in."""
    assert first_lineno <= pairs[0][1]
    cur_byte, cur_line = 0, first_lineno
    for byte_off, line_off in pairs:
        byte_delta = byte_off - cur_byte
        line_delta = line_off - cur_line
        assert byte_delta >= 0
        assert line_delta >= 0
        while byte_delta > 255:
            yield 255 # byte
            yield 0   # line
            byte_delta -= 255
        yield byte_delta
        while line_delta > 255:
            yield 255 # line
            yield 0   # byte
            line_delta -= 255
        yield line_delta
        cur_byte, cur_line = byte_off, line_off

def lnotab_string(pairs, first_lineno=0):
    return "".join(chr(b) for b in lnotab(pairs, first_lineno))

def byte_pairs(lnotab):
    """Yield pairs of integers from a string."""
    for i in range(0, len(lnotab), 2):
        yield ord(lnotab[i]), ord(lnotab[i+1])
        
def lnotab_numbers(lnotab, first_lineno=0):
    """Yields the byte, line offset pairs from a packed lnotab string."""

    last_line = None
    cur_byte, cur_line = 0, first_lineno
    for byte_delta, line_delta in byte_pairs(lnotab):
        if byte_delta:
            if cur_line != last_line:
                yield cur_byte, cur_line
                last_line = cur_line
            cur_byte += byte_delta
        cur_line += line_delta
    if cur_line != last_line:        
        yield cur_byte, cur_line
    

## Tests

def same_list(a, b):
    a = list(a)
    assert a == b
    
def test_simple():
    same_list(lnotab([(0,1)]), [0, 1])
    same_list(lnotab([(0,1), (6, 2)]), [0, 1,  6, 1])

def test_starting_above_one():
    same_list(lnotab([(0,100), (6,101)]), [0, 100,  6, 1])
    same_list(lnotab([(0,100), (6,101)], 50), [0, 50,  6, 1])
    
def test_large_gaps():
    same_list(lnotab([(0,1), (300, 300)]), [0, 1,  255, 0,  45, 255,  0, 44])
    same_list(lnotab([(0,1), (255, 300)]), [0, 1,  255, 255,  0, 44])
    same_list(lnotab([(0,1), (255, 256)]), [0, 1,  255, 255])
    
def test_strings():
    assert lnotab_string([(0,1), (6, 2)]) == "\x00\x01\x06\x01"
    assert lnotab_string([(0,1), (300, 300)]) == "\x00\x01\xff\x00\x2d\xff\x00\x2c"

def test_numbers():
    same_list(lnotab_numbers("\x00\x01\x06\x01"), [(0,1), (6,2)])
    same_list(lnotab_numbers("\x00\x01\xff\x00\x2d\xff\x00\x2c"), [(0,1), (300, 300)])

def test_numbers_firstlineno():
    same_list(lnotab_numbers("\x00\x01\xff\x00\x2d\xff\x00\x2c", 10), [(0,11), (300, 310)])
