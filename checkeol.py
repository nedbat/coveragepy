# Check files for incorrect newlines

import fnmatch, os

def check_file(fname):
    for n, line in enumerate(open(fname, "rb")):
        if "\r" in line:
            print "%s@%d: CR found" % (fname, n)
            return

def check_files(root, patterns):
    for root, dirs, files in os.walk(root):
        for f in files:
            fname = os.path.join(root, f)
            for p in patterns:
                if fnmatch.fnmatch(fname, p):
                    check_file(fname)
                    break
        if '.svn' in dirs:
            dirs.remove('.svn')

check_files("coverage", ["*.py"])
check_files("test", ["*.py", "*,cover"])
check_file("setup.py")
