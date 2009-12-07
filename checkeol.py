# Check files for incorrect newlines and trailing whitespace.

import fnmatch, os

def check_file(fname, crlf=True, trail_white=True):
    for n, line in enumerate(open(fname, "rb")):
        if crlf:
            if "\r" in line:
                print "%s@%d: CR found" % (fname, n+1)
                return
        if trail_white:
            line = line[:-1]
            if line.rstrip() != line:
                print "%s@%d: trailing whitespace found" % (fname, n+1)
                return


def check_files(root, patterns, **kwargs):
    for root, dirs, files in os.walk(root):
        for f in files:
            fname = os.path.join(root, f)
            for p in patterns:
                if fnmatch.fnmatch(fname, p):
                    check_file(fname, **kwargs)
                    break
        for pattern in ['.svn', '.hg']:
            if pattern in dirs:
                dirs.remove(pattern)


check_files("coverage", ["*.py"])
check_files("coverage/htmlfiles", ["*.html", "*.css", "*.js"])
check_files("test", ["*.py"])
check_files("test", ["*,cover"], trail_white=False)
check_file("setup.py")
check_files(".", ["*.txt"])
