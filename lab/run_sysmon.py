# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Run sys.monitoring on a file of Python code."""

import functools
import sys

print(sys.version)
the_program = sys.argv[1]

code = open(the_program).read()

my_id = sys.monitoring.COVERAGE_ID
sys.monitoring.use_tool_id(my_id, "run_sysmon.py")
register = functools.partial(sys.monitoring.register_callback, my_id)
events = sys.monitoring.events


def bytes_to_lines(code):
    """Make a dict mapping byte code offsets to line numbers."""
    b2l = {}
    cur_line = 0
    for bstart, bend, lineno in code.co_lines():
        for boffset in range(bstart, bend, 2):
            b2l[boffset] = lineno
    return b2l


def sysmon_py_start(code, instruction_offset):
    print(f"PY_START: {code.co_filename}@{instruction_offset}")
    sys.monitoring.set_local_events(
        my_id,
        code,
        events.PY_RETURN | events.PY_RESUME | events.LINE | events.BRANCH | events.JUMP,
    )


def sysmon_py_resume(code, instruction_offset):
    b2l = bytes_to_lines(code)
    print(
        f"PY_RESUME: {code.co_filename}@{instruction_offset}, "
        + f"{b2l[instruction_offset]}"
    )


def sysmon_py_return(code, instruction_offset, retval):
    b2l = bytes_to_lines(code)
    print(
        f"PY_RETURN: {code.co_filename}@{instruction_offset}, "
        + f"{b2l[instruction_offset]}"
    )


def sysmon_line(code, line_number):
    print(f"LINE: {code.co_filename}@{line_number}")
    return sys.monitoring.DISABLE


def sysmon_branch(code, instruction_offset, destination_offset):
    b2l = bytes_to_lines(code)
    print(
        f"BRANCH: {code.co_filename}@{instruction_offset}->{destination_offset}, "
        + f"{b2l[instruction_offset]}->{b2l[destination_offset]}"
    )


def sysmon_jump(code, instruction_offset, destination_offset):
    b2l = bytes_to_lines(code)
    print(
        f"JUMP: {code.co_filename}@{instruction_offset}->{destination_offset}, "
        + f"{b2l[instruction_offset]}->{b2l[destination_offset]}"
    )


sys.monitoring.set_events(
    my_id,
    events.PY_START | events.PY_UNWIND,
)
register(events.PY_START, sysmon_py_start)
register(events.PY_RESUME, sysmon_py_resume)
register(events.PY_RETURN, sysmon_py_return)
# register(events.PY_UNWIND, sysmon_py_unwind_arcs)
register(events.LINE, sysmon_line)
register(events.BRANCH, sysmon_branch)
register(events.JUMP, sysmon_jump)

exec(code)
