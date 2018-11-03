#!/usr/bin/env python3
#
# Run this like:
#
#   $ $(lab/set_env.py)
#

import functools
import glob
import itertools
import os
import re
import sys

pstderr = functools.partial(print, file=sys.stderr)

SETTINGS = []

line_pattern = r"\$set_env.py: (\w+) - (.*)"
globs = "*/*.py *.py"

filenames = itertools.chain.from_iterable(glob.glob(g) for g in globs.split())
files = 0
for filename in filenames:
    files += 1
    with open(filename) as f:
        for line in f:
            m = re.search(line_pattern, line)
            if m:
                SETTINGS.append(m.groups())
pstderr("Read {} files".format(files))


def read_them():
    values = {}
    for name, _ in SETTINGS:
        values[name] = os.environ.get(name)
    return values

def show_them(values):
    for i, (name, description) in enumerate(SETTINGS, start=1):
        value = values[name]
        if value is None:
            eq = ' '
            value = ''
        else:
            eq = '='
            value = repr(value)
        pstderr("{:2d}: {:>30s} {} {:12s}   {}".format(i, name, eq, value, description))

def set_by_num(values, n, value):
    setting_name = SETTINGS[int(n)-1][0]
    values[setting_name] = value

def get_new_values(values):
    show = True
    while True:
        if show:
            show_them(values)
            show = False
            pstderr("")
        pstderr("> ", end='')
        sys.stderr.flush()
        try:
            cmd = input("").strip().split(None, 1)
        except EOFError:
            pstderr("\n")
            break
        if not cmd:
            continue
        if cmd[0] == 'q':
            break
        if cmd[0] == 'x':
            set_by_num(values, cmd[1], None)
        else:
            try:
                nsetting = int(cmd[0])
            except ValueError:
                pass
            else:
                set_by_num(values, nsetting, cmd[1])
        show = True

    return values

def as_exports(values):
    exports = []
    for name, value in values.items():
        if value is None:
            exports.append("export -n {}".format(name))
        else:
            exports.append("export {}={!r}".format(name, value))
    return "eval " + "; ".join(exports)

print(as_exports(get_new_values(read_them())))
