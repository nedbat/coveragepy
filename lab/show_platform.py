import platform
import types

for n in dir(platform):
    if n.startswith("_"):
        continue
    v = getattr(platform, n)
    if isinstance(v, types.ModuleType):
        continue
    if callable(v):
        try:
            v = v()
            n += "()"
        except:
            continue
    print "%30s: %r" % (n, v)
