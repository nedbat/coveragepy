"""Helper for building, testing, and linting coverage.py.

To get portability, all these operations are written in Python here instead
of in shell scripts, batch files, or Makefiles.

"""

import fnmatch
import os
import sys
import zipfile

def do_remove_extension(args):
    """Remove the compiled C extension, no matter what its name."""

    so_names = """
        tracer.so
        tracer.cpython-32m.so
        """.split()

    for filename in so_names:
        try:
            os.remove(os.path.join("coverage", filename))
        except OSError:
            pass

def do_test_with_tracer(args):
    """Run nosetests with a particular tracer."""
    import nose.core
    os.environ["COVERAGE_TEST_TRACER"] = args[0]
    nose_args = ["nosetests"] + args[1:]
    nose.core.main(argv=nose_args)

def do_zip_mods(args):
    """Build the zipmods.zip file."""
    zf = zipfile.ZipFile("test/zipmods.zip", "w")
    zf.write("test/covmodzip1.py", "covmodzip1.py")

def do_check_eol(args):
    """Check files for incorrect newlines and trailing whitespace."""

    ignore_dirs = ['.svn', '.hg', '.tox']

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
            for pattern in ignore_dirs:
                if pattern in dirs:
                    dirs.remove(pattern)

    check_files("coverage", ["*.py", "*.c"])
    check_files("coverage/htmlfiles", ["*.html", "*.css", "*.js"])
    check_files("test", ["*.py"])
    check_files("test", ["*,cover"], trail_white=False)
    check_files("test/js", ["*.js", "*.html"])
    check_file("setup.py")
    check_files("doc", ["*.rst"])
    check_files(".", ["*.txt"])


def main(args):
    handler = globals().get('do_'+args[0])
    if handler is None:
        print("*** No handler for %r" % args[0])
        return 1
    return handler(args[1:])

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
