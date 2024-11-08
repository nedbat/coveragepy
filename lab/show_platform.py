# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

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
    print(f"{n:>30}: {v!r}")
