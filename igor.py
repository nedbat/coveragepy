"""Helper for building, testing, and linting coverage.py.

To get portability, all these operations are written in Python here instead
of in shell scripts, batch files, or Makefiles.

"""

import fnmatch
import glob
import inspect
import os
import platform
import socket
import sys
import warnings
import zipfile


warnings.simplefilter("default")


# Functions named do_* are executable from the command line: do_blah is run
# by "python igor.py blah".


def do_remove_extension():
    """Remove the compiled C extension, no matter what its name."""

    so_patterns = """
        tracer.so
        tracer.*.so
        tracer.pyd
        """.split()

    for pattern in so_patterns:
        pattern = os.path.join("coverage", pattern)
        for filename in glob.glob(pattern):
            try:
                os.remove(filename)
            except OSError:
                pass

def run_tests(tracer, *nose_args):
    """The actual running of tests."""
    import nose.core
    if tracer == "py":
        label = "with Python tracer"
        skipper = os.environ.get("COVERAGE_NO_PYTRACER")
    else:
        label = "with C tracer"
        skipper = os.environ.get("COVERAGE_NO_EXTENSION")

    if skipper:
        msg = "Skipping tests " + label
        if len(skipper) > 1:
            msg += ": " + skipper
        print(msg)
        return

    print_banner(label)
    os.environ["COVERAGE_TEST_TRACER"] = tracer
    nose_args = ["nosetests"] + list(nose_args)
    nose.core.main(argv=nose_args)

def run_tests_with_coverage(tracer, *nose_args):
    """Run tests, but with coverage."""
    import coverage

    os.environ['COVERAGE_PROCESS_START'] = os.path.abspath('metacov.ini')
    os.environ['COVERAGE_HOME'] = os.getcwd()

    # Create the .pth file that will let us measure coverage in sub-processes.
    # The .pth file seems to have to be alphabetically after easy-install.pth
    # or the sys.path entries aren't created right?
    import nose
    pth_dir = os.path.dirname(os.path.dirname(nose.__file__))
    pth_path = os.path.join(pth_dir, "zzz_metacov.pth")
    with open(pth_path, "w") as pth_file:
        pth_file.write("import coverage; coverage.process_startup()\n")

    version = "%s%s" % sys.version_info[:2]
    suffix = "%s_%s_%s" % (version, tracer, socket.gethostname())

    cov = coverage.coverage(config_file="metacov.ini", data_suffix=suffix)
    # Cheap trick: the coverage code itself is excluded from measurement, but
    # if we clobber the cover_prefix in the coverage object, we can defeat the
    # self-detection.
    cov.cover_prefix = "Please measure coverage.py!"
    cov._warn_unimported_source = False
    cov.erase()
    cov.start()

    try:
        # Re-import coverage to get it coverage tested!  I don't understand all
        # the mechanics here, but if I don't carry over the imported modules
        # (in covmods), then things go haywire (os == None, eventually).
        covmods = {}
        covdir = os.path.split(coverage.__file__)[0]
        # We have to make a list since we'll be deleting in the loop.
        modules = list(sys.modules.items())
        for name, mod in modules:
            if name.startswith('coverage'):
                if getattr(mod, '__file__', "??").startswith(covdir):
                    covmods[name] = mod
                    del sys.modules[name]
        import coverage     # don't warn about re-import: pylint: disable=reimported
        sys.modules.update(covmods)

        # Run nosetests, with the arguments from our command line.
        try:
            run_tests(tracer, *nose_args)
        except SystemExit:
            # nose3 seems to raise SystemExit, not sure why?
            pass
    finally:
        cov.stop()
        os.remove(pth_path)

    cov.save()

def do_combine_html():
    """Combine data from a meta-coverage run, and make the HTML report."""
    import coverage
    os.environ['COVERAGE_HOME'] = os.getcwd()
    cov = coverage.coverage(config_file="metacov.ini")
    cov.load()
    cov.combine()
    cov.save()
    cov.html_report()

def do_test_with_tracer(tracer, *noseargs):
    """Run nosetests with a particular tracer."""
    if os.environ.get("COVERAGE_COVERAGE", ""):
        return run_tests_with_coverage(tracer, *noseargs)
    else:
        return run_tests(tracer, *noseargs)

def do_zip_mods():
    """Build the zipmods.zip file."""
    zf = zipfile.ZipFile("tests/zipmods.zip", "w")
    zf.write("tests/covmodzip1.py", "covmodzip1.py")
    zf.close()

def do_install_egg():
    """Install the egg1 egg for tests."""
    # I am pretty certain there are easier ways to install eggs...
    # pylint: disable=import-error,no-name-in-module
    import distutils.core
    cur_dir = os.getcwd()
    os.chdir("tests/eggsrc")
    distutils.core.run_setup("setup.py", ["--quiet", "bdist_egg"])
    egg = glob.glob("dist/*.egg")[0]
    distutils.core.run_setup(
        "setup.py", ["--quiet", "easy_install", "--no-deps", "--zip-ok", egg]
        )
    os.chdir(cur_dir)

def do_check_eol():
    """Check files for incorrect newlines and trailing whitespace."""

    ignore_dirs = [
        '.svn', '.hg', '.tox', '.tox_kits', 'coverage.egg-info',
        '_build', 'covtestegg1.egg-info',
        ]
    checked = set([])

    def check_file(fname, crlf=True, trail_white=True):
        """Check a single file for whitespace abuse."""
        fname = os.path.relpath(fname)
        if fname in checked:
            return
        checked.add(fname)

        line = None
        with open(fname, "rb") as f:
            for n, line in enumerate(f, start=1):
                if crlf:
                    if "\r" in line:
                        print("%s@%d: CR found" % (fname, n))
                        return
                if trail_white:
                    line = line[:-1]
                    if not crlf:
                        line = line.rstrip('\r')
                    if line.rstrip() != line:
                        print("%s@%d: trailing whitespace found" % (fname, n))
                        return

        if line is not None and not line.strip():
            print("%s: final blank line" % (fname,))

    def check_files(root, patterns, **kwargs):
        """Check a number of files for whitespace abuse."""
        for root, dirs, files in os.walk(root):
            for f in files:
                fname = os.path.join(root, f)
                for p in patterns:
                    if fnmatch.fnmatch(fname, p):
                        check_file(fname, **kwargs)
                        break
            for dir_name in ignore_dirs:
                if dir_name in dirs:
                    dirs.remove(dir_name)

    check_files("coverage", ["*.py", "*.c"])
    check_files("coverage/htmlfiles", ["*.html", "*.css", "*.js"])
    check_file("tests/farm/html/src/bom.py", crlf=False)
    check_files("tests", ["*.py"])
    check_files("tests", ["*,cover"], trail_white=False)
    check_files("tests/js", ["*.js", "*.html"])
    check_file("setup.py")
    check_file("igor.py")
    check_file("Makefile")
    check_file(".hgignore")
    check_file(".travis.yml")
    check_files("doc", ["*.rst"])
    check_files(".", ["*.txt"])


def print_banner(label):
    """Print the version of Python."""
    try:
        impl = platform.python_implementation()
    except AttributeError:
        impl = "Python"

    version = platform.python_version()

    if '__pypy__' in sys.builtin_module_names:
        pypy_version = sys.pypy_version_info
        version += " (pypy %s)" % ".".join(str(v) for v in pypy_version)

    which_python = os.path.relpath(sys.executable)
    print('=== %s %s %s (%s) ===' % (impl, version, label, which_python))


def do_help():
    """List the available commands"""
    items = list(globals().items())
    items.sort()
    for name, value in items:
        if name.startswith('do_'):
            print("%-20s%s" % (name[3:], value.__doc__))


def main(args):
    """Main command-line execution for igor.

    Verbs are taken from the command line, and extra words taken as directed
    by the arguments needed by the handler.

    """
    while args:
        verb = args.pop(0)
        handler = globals().get('do_'+verb)
        if handler is None:
            print("*** No handler for %r" % verb)
            return 1
        argspec = inspect.getargspec(handler)
        if argspec[1]:
            # Handler has *args, give it all the rest of the command line.
            handler_args = args
            args = []
        else:
            # Handler has specific arguments, give it only what it needs.
            num_args = len(argspec[0])
            handler_args = args[:num_args]
            args = args[num_args:]
        ret = handler(*handler_args)
        # If a handler returns a failure-like value, stop.
        if ret:
            return ret

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
