# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Raw data collector for coverage.py."""

from __future__ import annotations

import atexit
import dataclasses
import dis
import inspect
import os
import os.path
import re
import sys
import threading
import traceback

from types import CodeType, FrameType, ModuleType
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, cast

#from coverage.debug import short_stack
from coverage.types import (
    TArc, TFileDisposition, TLineNo, TTraceData, TTraceFileData, TTraceFn,
    TTracer, TWarnFn,
)

# When running meta-coverage, this file can try to trace itself, which confuses
# everything.  Don't trace ourselves.

THIS_FILE = __file__.rstrip("co")

seen_threads = set()

def log(msg):
    return
    # Thread ids are reused across processes? Make a shorter number more likely
    # to be unique.
    pid = os.getpid()
    tid = (os.getpid() * threading.current_thread().ident) % 9_999_991
    tid = f"{tid:07d}"
    if tid not in seen_threads:
        seen_threads.add(tid)
        log(f"New thread {tid}:\n{short_stack(full=True)}")
    for filename in [
        "/tmp/pan.out",
        f"/tmp/pan-{pid}.out",
        f"/tmp/pan-{pid}-{tid}.out",
    ]:
        with open(filename, "a") as f:
            print(f"{pid}:{tid}: {msg}", file=f, flush=True)

FILENAME_REGEXES = [
    (r"/private/var/folders/.*/pytest-of-.*/pytest-\d+", "tmp:"),
]
FILENAME_SUBS = []

def fname_repr(filename):
    if not FILENAME_SUBS:
        for pathdir in sys.path:
            FILENAME_SUBS.append((pathdir, "syspath:"))
        import coverage
        FILENAME_SUBS.append((os.path.dirname(coverage.__file__), "cov:"))
        FILENAME_SUBS.sort(key=(lambda pair: len(pair[0])), reverse=True)
    if filename is not None:
        for pat, sub in FILENAME_REGEXES:
            filename = re.sub(pat, sub, filename)
        for before, after in FILENAME_SUBS:
            filename = filename.replace(before, after)
    return repr(filename)

def arg_repr(arg):
    if isinstance(arg, CodeType):
        arg_repr = f"<name={arg.co_name}, file={fname_repr(arg.co_filename)}#{arg.co_firstlineno}>"
    else:
        arg_repr = repr(arg)
    return arg_repr

def short_stack(full=True):
    stack: Iterable[inspect.FrameInfo] = inspect.stack()[::-1]
    return "\n".join(f"{fi.function:>30s} : 0x{id(fi.frame):x} {fi.filename}:{fi.lineno}" for fi in stack)

def panopticon(*names):
    def _decorator(meth):
        def _wrapped(self, *args):
            try:
                # log("stack:\n" + short_stack())
                # args_reprs = []
                # for name, arg in zip(names, args):
                #     if name is None:
                #         continue
                #     args_reprs.append(f"{name}={arg_repr(arg)}")
                # log(f"{id(self)}:{meth.__name__}({', '.join(args_reprs)})")
                ret = meth(self, *args)
                # log(f" end {id(self)}:{meth.__name__}({', '.join(args_reprs)})")
                return ret
            except Exception as exc:
                log(f"{exc.__class__.__name__}: {exc}")
                with open("/tmp/pan.out", "a") as f:
                    traceback.print_exception(exc, file=f)
                sys.monitoring.set_events(sys.monitoring.COVERAGE_ID, 0)
                raise
        return _wrapped
    return _decorator


@dataclasses.dataclass
class CodeInfo:
    tracing: bool
    file_data: Optional[TTraceFileData]
    byte_to_line: Dict[int, int]


def bytes_to_lines(code):
    b2l = {}
    cur_line = None
    for inst in dis.get_instructions(code):
        if inst.starts_line is not None:
            cur_line = inst.starts_line
        b2l[inst.offset] = cur_line
    log(f"  --> bytes_to_lines: {b2l!r}")
    return b2l

class Pep669Tracer(TTracer):
    """Python implementation of the raw data tracer for PEP669 implementations."""
    # One of these will be used across threads. Be careful.

    def __init__(self) -> None:
        log(f"Pep669Tracer.__init__: @{id(self)}\n{short_stack()}")
        # pylint: disable=super-init-not-called
        # Attributes set from the collector:
        self.data: TTraceData
        self.trace_arcs = False
        self.should_trace: Callable[[str, FrameType], TFileDisposition]
        self.should_trace_cache: Dict[str, Optional[TFileDisposition]]
        self.should_start_context: Optional[Callable[[FrameType], Optional[str]]] = None
        self.switch_context: Optional[Callable[[Optional[str]], None]] = None
        self.warn: TWarnFn

        # The threading module to use, if any.
        self.threading: Optional[ModuleType] = None

        self.code_infos: Dict[CodeType, CodeInfo] = {}
        self.last_lines: Dict[FrameType, int] = {}
        self.stats = {
            "starts": 0,
        }

        self.thread: Optional[threading.Thread] = None
        self.stopped = False
        self._activity = False

        self.in_atexit = False
        # On exit, self.in_atexit = True
        atexit.register(setattr, self, "in_atexit", True)

    def __repr__(self) -> str:
        me = id(self)
        points = sum(len(v) for v in self.data.values())
        files = len(self.data)
        return f"<Pep669Tracer at 0x{me:x}: {points} data points in {files} files>"

    def start(self) -> TTraceFn:    # TODO: wrong return type
        """Start this Tracer."""
        self.stopped = False
        if self.threading:
            if self.thread is None:
                self.thread = self.threading.current_thread()
            else:
                if self.thread.ident != self.threading.current_thread().ident:
                    # Re-starting from a different thread!? Don't set the trace
                    # function, but we are marked as running again, so maybe it
                    # will be ok?
                    1/0
                    return self._cached_bound_method_trace

        self.myid = sys.monitoring.COVERAGE_ID
        sys.monitoring.use_tool_id(self.myid, "coverage.py")
        events = sys.monitoring.events
        sys.monitoring.set_events(
            self.myid,
            events.PY_START | events.PY_RETURN | events.PY_RESUME | events.PY_YIELD | events.PY_UNWIND,
        )
        sys.monitoring.register_callback(self.myid, events.PY_START, self.sysmon_py_start)
        sys.monitoring.register_callback(self.myid, events.PY_RESUME, self.sysmon_py_resume)
        sys.monitoring.register_callback(self.myid, events.PY_RETURN, self.sysmon_py_return)
        sys.monitoring.register_callback(self.myid, events.PY_YIELD, self.sysmon_py_yield)
        sys.monitoring.register_callback(self.myid, events.PY_UNWIND, self.sysmon_py_unwind)
        sys.monitoring.register_callback(self.myid, events.LINE, self.sysmon_line)
        sys.monitoring.register_callback(self.myid, events.BRANCH, self.sysmon_branch)
        sys.monitoring.register_callback(self.myid, events.JUMP, self.sysmon_jump)

    def stop(self) -> None:
        """Stop this Tracer."""
        sys.monitoring.set_events(self.myid, 0)
        sys.monitoring.free_tool_id(self.myid)

    def activity(self) -> bool:
        """Has there been any activity?"""
        return self._activity

    def reset_activity(self) -> None:
        """Reset the activity() flag."""
        self._activity = False

    def get_stats(self) -> Optional[Dict[str, int]]:
        """Return a dictionary of statistics, or None."""
        return None
        return self.stats | {
            "codes": len(self.code_infos),
            "codes_tracing": sum(1 for ci in self.code_infos.values() if ci.tracing),
        }

    def callers_frame(self) -> FrameType:
        return inspect.currentframe().f_back.f_back.f_back

    @panopticon("code", "@")
    def sysmon_py_start(self, code, instruction_offset: int):
        # Entering a new frame.  Decide if we should trace in this file.
        self._activity = True
        self.stats["starts"] += 1

        code_info = self.code_infos.get(code)
        if code_info is not None:
            tracing_code = code_info.tracing
            file_data = code_info.file_data
        else:
            tracing_code = file_data = None

        if tracing_code is None:
            filename = code.co_filename
            disp = self.should_trace_cache.get(filename)
            if disp is None:
                frame = inspect.currentframe().f_back.f_back
                disp = self.should_trace(filename, frame)
                self.should_trace_cache[filename] = disp

            tracing_code = disp.trace
            if tracing_code:
                tracename = disp.source_filename
                assert tracename is not None
                if tracename not in self.data:
                    self.data[tracename] = set()    # type: ignore[assignment]
                file_data = self.data[tracename]
                b2l = bytes_to_lines(code)
            else:
                file_data = None
                b2l = None

            self.code_infos[code] = CodeInfo(
                tracing=tracing_code,
                file_data=file_data,
                byte_to_line=b2l,
            )

            if tracing_code:
                events = sys.monitoring.events
                log(f"set_local_events(code={arg_repr(code)})")
                sys.monitoring.set_local_events(
                    self.myid,
                    code,
                    sys.monitoring.events.LINE |
                    sys.monitoring.events.BRANCH |
                    sys.monitoring.events.JUMP,
                )

        if tracing_code:
            frame = self.callers_frame()
            self.last_lines[frame] = -code.co_firstlineno
        log(f"   {file_data=}")

    @panopticon("code", "@")
    def sysmon_py_resume(self, code, instruction_offset: int):
        frame = self.callers_frame()
        self.last_lines[frame] = frame.f_lineno

    @panopticon("code", "@", None)
    def sysmon_py_return(self, code, instruction_offset: int, retval: object):
        frame = self.callers_frame()
        code_info = self.code_infos.get(code)
        if code_info is not None and code_info.file_data is not None:
            if self.trace_arcs:
                arc = (self.last_lines[frame], -code.co_firstlineno)
                cast(Set[TArc], code_info.file_data).add(arc)
                log(f"   add1({arc=})")

        # Leaving this function, no need for the frame any more.
        log(f"   popping frame 0x{id(frame):x}")
        self.last_lines.pop(frame, None)

    @panopticon("code", "@", None)
    def sysmon_py_yield(self, code, instruction_offset: int, retval: object):
        pass

    @panopticon("code", "@", None)
    def sysmon_py_unwind(self, code, instruction_offset: int, exception):
        frame = self.callers_frame()
        code_info = self.code_infos[code]
        if code_info.file_data is not None:
            if self.trace_arcs:
                arc = (self.last_lines[frame], -code.co_firstlineno)
                cast(Set[TArc], code_info.file_data).add(arc)
                log(f"   add3({arc=})")

        # Leaving this function.
        self.last_lines.pop(frame, None)

    @panopticon("code", "line")
    def sysmon_line(self, code, line_number: int):
        frame = self.callers_frame()
        code_info = self.code_infos[code]
        if code_info.file_data is not None:
            if self.trace_arcs:
                arc = (self.last_lines[frame], line_number)
                cast(Set[TArc], code_info.file_data).add(arc)
                log(f"   add4({arc=})")
            else:
                cast(Set[TLineNo], code_info.file_data).add(line_number)
                log(f"   add5({line_number=})")
            self.last_lines[frame] = line_number

    @panopticon("code", "from@", "to@")
    def sysmon_branch(self, code, instruction_offset: int, destination_offset: int):
        ...

    @panopticon("code", "from@", "to@")
    def sysmon_jump(self, code, instruction_offset: int, destination_offset: int):
        ...
