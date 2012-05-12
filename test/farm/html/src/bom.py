# A python source file in utf-8, with BOM
math = "3×4 = 12, ÷2 = 6±0"

import sys

if sys.version_info >= (3, 0):
    assert len(math) == 18
    assert len(math.encode('utf-8')) == 21
else:
    assert len(math) == 21
    assert len(math.decode('utf-8')) == 18
