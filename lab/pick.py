# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""
Pick lines from a file.  Blank or commented lines are ignored.

Used to subset lists of tests to run.  Use with the --select-cmd pytest plugin
option.

Get a list of test nodes::

    .tox/py311/bin/pytest --collect-only | grep :: > tests.txt

Use like this::

    pytest --select-cmd="python lab/pick.py sample 10 < tests.txt"

as in::

    te py311 -- -vvv -n 0 --cache-clear --select-cmd="python lab/pick.py sample 10 < tests.txt"

or::

    for n in 1 1 2 2 3 3; do te py311 -- -vvv -n 0 --cache-clear --select-cmd="python lab/pick.py sample 3 $n < tests.txt"; done

or::

    for n in $(seq 1 10); do echo seed=$n; COVERAGE_COVERAGE=yes te py311 -- -n 0 --cache-clear --select-cmd="python lab/pick.py sample 20 $n < tests.txt"; done

"""

import random
import sys

args = sys.argv[1:][::-1]
next_arg = args.pop

lines = []
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    if line.startswith("#"):
        continue
    lines.append(line)

mode = next_arg()
if mode == "head":
    number = int(next_arg())
    lines = lines[:number]
elif mode == "sample":
    number = int(next_arg())
    if args:
        random.seed(next_arg())
    lines = random.sample(lines, number)
elif mode == "all":
    pass
else:
    raise ValueError(f"Don't know {mode=}")

for line in lines:
    print(line)
