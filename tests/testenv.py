# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Environment settings affecting tests."""

from __future__ import annotations

import os

# Are we testing the C-implemented trace function?
C_TRACER = os.getenv("COVERAGE_CORE", "ctrace") == "ctrace"
