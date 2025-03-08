# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Environment settings affecting tests."""

from __future__ import annotations

from coverage import env

# Are we testing the C-implemented trace function?
C_TRACER = env.getenv("COVERAGE_CORE", "ctrace") == "ctrace"

# Are we testing the Python-implemented trace function?
PY_TRACER = env.getenv("COVERAGE_CORE", "ctrace") == "pytrace"

# Are we testing the sys.monitoring implementation?
SYS_MON = env.getenv("COVERAGE_CORE", "ctrace") == "sysmon"

# Are we using a settrace function as a core?
SETTRACE_CORE = C_TRACER or PY_TRACER

# Are plugins supported during these tests?
PLUGINS = C_TRACER

# Are dynamic contexts supported during these tests?
DYN_CONTEXTS = C_TRACER or PY_TRACER
