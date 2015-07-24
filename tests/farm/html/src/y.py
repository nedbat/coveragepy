# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

# A test file for XML reporting by coverage.py.

def choice(x):
    if x < 2:
        return 3
    else:
        return 4

assert choice(1) == 3
