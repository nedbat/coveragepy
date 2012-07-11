"""Helper for building, testing, and linting coverage.py.

To get portability, all these operations are written in Python here instead
of in shell scripts, batch files, or Makefiles.

"""

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


def main(args):
    handler = globals().get('do_'+args[0])
    if handler is None:
        print("*** No handler for %r" % args[0])
        return 1
    return handler(args[1:])

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
