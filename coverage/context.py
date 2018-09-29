# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Determine contexts for coverage.py"""

def should_start_context_test_function(frame):
    """Is this frame calling a test_* function?"""
    fn_name = frame.f_code.co_name
    if fn_name.startswith("test"):
        return qualname_from_frame(frame)
    return None


def qualname_from_frame(frame):
    """Get a qualified name for the code running in `frame`."""
    co = frame.f_code
    fname = co.co_name
    if not co.co_varnames:
        return fname

    locs = frame.f_locals
    first_arg = co.co_varnames[0]
    if co.co_argcount and first_arg == "self":
        self = locs["self"]
    #elif co.co_flags & 0x04:    # *args syntax
    #    self = locs[first_arg][0]
    else:
        return fname

    method = getattr(self, fname, None)
    if method is None:
        return fname

    func = method.__func__
    if hasattr(func, '__qualname__'):
        qname = func.__qualname__
    else:
        for cls in self.__class__.__mro__:
            f = cls.__dict__.get(fname, None)
            if f is None:
                continue
            if f is func:
                qname = cls.__name__ + "." + fname
                break
        else:
            qname = fname
    return qname
