# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

# A test file for HTML reporting by coverage.py.

if 1 < 2:
    # Needed a < to look at HTML entities.
    a = 3
else:
    a = 4
