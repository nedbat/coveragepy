class Parent:
    def meth(self):
        print("METH")

class Child(Parent):
    pass

def trace(frame, event, args):
    # Thanks to Aleksi Torhamo for code and idea.
    co = frame.f_code
    fname = co.co_name
    if not co.co_varnames:
        return
    locs = frame.f_locals
    first_arg = co.co_varnames[0]
    if co.co_argcount:
        self = locs[first_arg]
    elif co.co_flags & 0x04:    # *args syntax
        self = locs[first_arg][0]
    else:
        return

    func = getattr(self, fname).__func__
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
    print(f"{event}: {self}.{fname} {qname}")
    return trace

import sys
sys.settrace(trace)

Child().meth()
