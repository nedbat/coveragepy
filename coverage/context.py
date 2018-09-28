# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Determine contexts for coverage.py"""

def should_start_context_test_function(frame):
    """Is this frame calling a test_* function?"""
    fn_name = frame.f_code.co_name
    if fn_name.startswith("test"):
        return fn_name
    return None
