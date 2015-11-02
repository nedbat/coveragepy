#!/usr/bin/env python
"""
Run this file two ways under coverage and see that the times are the same:

    $ coverage run lab/bug397.py slow
    Runtime per example: 130.96 +/- 3.70 us
    $ coverage run lab/bug397.py fast
    Runtime per example: 131.34 +/- 4.48 us

Written by David MacIver as part of
https://bitbucket.org/ned/coveragepy/issues/397/stopping-and-resuming-coverage-with

"""
from __future__ import print_function

import sys
import random
import time
import math

if sys.argv[1] == "slow":
    sys.settrace(sys.gettrace())

random.seed(1)


def hash_str(s):
    h = 0
    for c in s:
        h = (h * 31 + ord(c)) & (2 ** 64 - 1)
    return h

data = [
    hex(random.getrandbits(1024)) for _ in range(500)
]

N_SAMPLES = 100


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs)


def sd(xs):
    return math.sqrt(mean(x ** 2 for x in xs) - mean(xs) ** 2)


if __name__ == '__main__':
    timing = []
    for _ in range(N_SAMPLES):
        start = time.time()
        for d in data:
            hash_str(d)
        timing.append(1000000 * (time.time() - start) / len(data))
    print("Runtime per example:", "%.2f +/- %.2f us" % (mean(timing), sd(timing)))
