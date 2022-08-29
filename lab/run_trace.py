# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Run a simple trace function on a file of Python code."""

from __future__ import annotations
import os, sys
from types import FrameType
from typing_extensions import Protocol

nest: int | None = 0


class _TraceType(Protocol):
    def __call__(self, frame: FrameType, event: str, arg: object) -> _TraceType | None:
        ...


def trace(frame: FrameType, event: str, arg: object) -> _TraceType | None:
    global nest

    if nest is None:
        # This can happen when Python is shutting down.
        return None

    print("%s%s %s %d @%d" % (
        "    " * nest,
        event,
        os.path.basename(frame.f_code.co_filename),
        frame.f_lineno,
        frame.f_lasti,
    ))

    if event == 'call':
        nest += 1
    if event == 'return':
        nest -= 1

    return trace

print(sys.version)
the_program = sys.argv[1]

code = open(the_program).read()
sys.settrace(trace)
exec(code)
