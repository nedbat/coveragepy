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

# Some other environment variables that could be useful:
# $set_env.py: PYTEST_ADDOPTS - Extra arguments to pytest.

pstderr = functools.partial(print, file=sys.stderr)

SETTINGS = []

def find_settings():
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
    SETTINGS.sort()
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

PROMPT = "(# value | x # | q) ::> "

def get_new_values(values):
    show = True
    while True:
        if show:
            show_them(values)
            show = False
            pstderr("")
        pstderr(PROMPT, end='')
        sys.stderr.flush()
        try:
            cmd = input("").strip().split()
        except EOFError:
            pstderr("\n")
            break
        if not cmd:
            continue
        if cmd[0] == 'q':
            break
        if cmd[0] == 'x':
            if len(cmd) < 2:
                pstderr("Need numbers of entries to delete")
                continue
            try:
                nums = map(int, cmd[1:])
            except ValueError:
                pstderr("Need numbers of entries to delete")
                continue
            else:
                for num in nums:
                    set_by_num(values, num, None)
        else:
            try:
                num = int(cmd[0])
            except ValueError:
                pstderr("Don't understand option {!r}".format(cmd[0]))
                continue
            else:
                if len(cmd) >= 2:
                    set_by_num(values, num, " ".join(cmd[1:]))
                else:
                    pstderr("Need a value to set")
                    continue
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

def main():
    find_settings()
    print(as_exports(get_new_values(read_them())))

if __name__ == '__main__':
    main()
