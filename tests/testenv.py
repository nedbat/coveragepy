# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Environment settings affecting tests."""

from __future__ import annotations

import os

REQUESTED_CORE = os.getenv("COVERAGE_CORE", "ctrace")

REQUESTED_TRACER_CLASS = {
    "ctrace": "CTracer",
    "pytrace": "PyTracer",
    "sysmon": "SysMonitor",
}[REQUESTED_CORE]

# Are we testing the C-implemented trace function?
C_TRACER = REQUESTED_CORE == "ctrace"

# Are we testing the Python-implemented trace function?
PY_TRACER = REQUESTED_CORE == "pytrace"

# Are we testing the sys.monitoring implementation?
SYS_MON = REQUESTED_CORE == "sysmon"

# Are we using a settrace function as a core?
SETTRACE_CORE = C_TRACER or PY_TRACER

# Are plugins supported during these tests?
PLUGINS = C_TRACER

# Are dynamic contexts supported during these tests?
DYN_CONTEXTS = C_TRACER or PY_TRACER
