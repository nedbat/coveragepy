# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Helper for building, testing, and linting coverage.py.

To get portability, all these operations are written in Python here instead
of in shell scripts, batch files, or Makefiles.

"""

import contextlib
import datetime
import fnmatch
import glob
import inspect
import os
import platform
import pprint
import re
import subprocess
import sys
import sysconfig
import textwrap
import types
import warnings
import zipfile

try:
    import pytest
except ImportError:
    # We want to be able to run this for some tasks that don't need pytest.
    pytest = None

# Constants derived the same as in coverage/env.py.  We can't import
# that file here, it would be evaluated too early and not get the
# settings we make in this file.

CPYTHON = (platform.python_implementation() == "CPython")
PYPY = (platform.python_implementation() == "PyPy")

@contextlib.contextmanager
def ignore_warnings():
    """Context manager to ignore warning within the with statement."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        yield


VERBOSITY = int(os.environ.get("COVERAGE_IGOR_VERBOSE", "0"))

# Functions named do_* are executable from the command line: do_blah is run
# by "python igor.py blah".


def do_show_env():
    """Show the environment variables."""
    print("Environment:")
    for env in sorted(os.environ):
        print(f"  {env} = {os.environ[env]!r}")


def do_remove_extension(*args):
    """Remove the compiled C extension, no matter what its name."""

    so_patterns = """
        tracer.so
        tracer.*.so
        tracer.pyd
        tracer.*.pyd
        """.split()

    if "--from-install" in args:
        # Get the install location using a subprocess to avoid
        # locking the file we are about to delete
        root = os.path.dirname(subprocess.check_output([
            sys.executable,
            "-Xutf8",
            "-c",
            "import coverage; print(coverage.__file__)"
        ], encoding="utf-8").strip())
    else:
        root = "coverage"

    for pattern in so_patterns:
        pattern = os.path.join(root, pattern.strip())
        if VERBOSITY:
            print(f"Searching for {pattern}")
        for filename in glob.glob(pattern):
            if os.path.exists(filename):
                if VERBOSITY:
                    print(f"Removing {filename}")
                try:
                    os.remove(filename)
                except OSError as exc:
                    if VERBOSITY:
                        print(f"Couldn't remove {filename}: {exc}")


def label_for_tracer(tracer):
    """Get the label for these tests."""
    if tracer == "py":
        label = "with Python tracer"
    else:
        label = "with C tracer"

    return label


def should_skip(tracer):
    """Is there a reason to skip these tests?"""
    skipper = ""

    # $set_env.py: COVERAGE_ONE_TRACER - Only run tests for one tracer.
    only_one = os.environ.get("COVERAGE_ONE_TRACER")
    if only_one:
        if CPYTHON:
            if tracer == "py":
                skipper = "Only one tracer: no Python tracer for CPython"
        else:
            if tracer == "c":
                skipper = f"No C tracer for {platform.python_implementation()}"
    elif tracer == "py":
        # $set_env.py: COVERAGE_NO_PYTRACER - Don't run the tests under the Python tracer.
        skipper = os.environ.get("COVERAGE_NO_PYTRACER")
    else:
        # $set_env.py: COVERAGE_NO_CTRACER - Don't run the tests under the C tracer.
        skipper = os.environ.get("COVERAGE_NO_CTRACER")

    if skipper:
        msg = "Skipping tests " + label_for_tracer(tracer)
        if len(skipper) > 1:
            msg += ": " + skipper
    else:
        msg = ""

    return msg


def make_env_id(tracer):
    """An environment id that will keep all the test runs distinct."""
    impl = platform.python_implementation().lower()
    version = "%s%s" % sys.version_info[:2]
    if PYPY:
        version += "_%s%s" % sys.pypy_version_info[:2]
    env_id = f"{impl}{version}_{tracer}"
    return env_id


def run_tests(tracer, *runner_args):
    """The actual running of tests."""
    if 'COVERAGE_TESTING' not in os.environ:
        os.environ['COVERAGE_TESTING'] = "True"
    print_banner(label_for_tracer(tracer))

    return pytest.main(list(runner_args))


def run_tests_with_coverage(tracer, *runner_args):
    """Run tests, but with coverage."""
    # Need to define this early enough that the first import of env.py sees it.
    os.environ['COVERAGE_TESTING'] = "True"
    os.environ['COVERAGE_PROCESS_START'] = os.path.abspath('metacov.ini')
    os.environ['COVERAGE_HOME'] = os.getcwd()
    context = os.environ.get('COVERAGE_CONTEXT')
    if context:
        os.environ['COVERAGE_CONTEXT'] = context + "." + tracer

    # Create the .pth file that will let us measure coverage in sub-processes.
    # The .pth file seems to have to be alphabetically after easy-install.pth
    # or the sys.path entries aren't created right?
    # There's an entry in "make clean" to get rid of this file.
    pth_dir = sysconfig.get_path("purelib")
    pth_path = os.path.join(pth_dir, "zzz_metacov.pth")
    with open(pth_path, "w") as pth_file:
        pth_file.write("import coverage; coverage.process_startup()\n")

    suffix = f"{make_env_id(tracer)}_{platform.platform()}"
    os.environ['COVERAGE_METAFILE'] = os.path.abspath(".metacov."+suffix)

    import coverage
    cov = coverage.Coverage(config_file="metacov.ini")
    cov._warn_unimported_source = False
    cov._warn_preimported_source = False
    cov.start()

    try:
        # Re-import coverage to get it coverage tested!  I don't understand all
        # the mechanics here, but if I don't carry over the imported modules
        # (in covmods), then things go haywire (os is None, eventually).
        covmods = {}
        covdir = os.path.split(coverage.__file__)[0]
        # We have to make a list since we'll be deleting in the loop.
        modules = list(sys.modules.items())
        for name, mod in modules:
            if name.startswith('coverage'):
                if getattr(mod, '__file__', "??").startswith(covdir):
                    covmods[name] = mod
                    del sys.modules[name]
        import coverage                         # pylint: disable=reimported
        sys.modules.update(covmods)

        # Run tests, with the arguments from our command line.
        status = run_tests(tracer, *runner_args)

    finally:
        cov.stop()
        os.remove(pth_path)

    cov.save()
    return status


def do_combine_html():
    """Combine data from a meta-coverage run, and make the HTML report."""
    import coverage
    os.environ['COVERAGE_HOME'] = os.getcwd()
    cov = coverage.Coverage(config_file="metacov.ini")
    cov.load()
    cov.combine()
    cov.save()
    show_contexts = bool(os.environ.get('COVERAGE_DYNCTX') or os.environ.get('COVERAGE_CONTEXT'))
    cov.html_report(show_contexts=show_contexts)


def do_test_with_tracer(tracer, *runner_args):
    """Run tests with a particular tracer."""
    # If we should skip these tests, skip them.
    skip_msg = should_skip(tracer)
    if skip_msg:
        print(skip_msg)
        return None

    os.environ["COVERAGE_TEST_TRACER"] = tracer
    if os.environ.get("COVERAGE_COVERAGE", "no") == "yes":
        return run_tests_with_coverage(tracer, *runner_args)
    else:
        return run_tests(tracer, *runner_args)


def do_zip_mods():
    """Build the zip files needed for tests."""
    with zipfile.ZipFile("tests/zipmods.zip", "w") as zf:

        # Take some files from disk.
        zf.write("tests/covmodzip1.py", "covmodzip1.py")

        # The others will be various encodings.
        source = textwrap.dedent("""\
            # coding: {encoding}
            text = u"{text}"
            ords = {ords}
            assert [ord(c) for c in text] == ords
            print(u"All OK with {encoding}")
            encoding = "{encoding}"
            """)
        # These encodings should match the list in tests/test_python.py
        details = [
            ('utf-8', 'ⓗⓔⓛⓛⓞ, ⓦⓞⓡⓛⓓ'),
            ('gb2312', '你好，世界'),
            ('hebrew', 'שלום, עולם'),
            ('shift_jis', 'こんにちは世界'),
            ('cp1252', '“hi”'),
        ]
        for encoding, text in details:
            filename = f'encoded_{encoding}.py'
            ords = [ord(c) for c in text]
            source_text = source.format(encoding=encoding, text=text, ords=ords)
            zf.writestr(filename, source_text.encode(encoding))

    with zipfile.ZipFile("tests/zip1.zip", "w") as zf:
        zf.write("tests/zipsrc/zip1/__init__.py", "zip1/__init__.py")
        zf.write("tests/zipsrc/zip1/zip1.py", "zip1/zip1.py")

    with zipfile.ZipFile("tests/covmain.zip", "w") as zf:
        zf.write("coverage/__main__.py", "__main__.py")


def do_check_eol():
    """Check files for incorrect newlines and trailing white space."""

    ignore_dirs = [
        '.svn', '.hg', '.git',
        '.tox*',
        '*.egg-info',
        '_build',
        '_spell',
        'tmp',
        'help',
    ]
    checked = set()

    def check_file(fname, crlf=True, trail_white=True):
        """Check a single file for white space abuse."""
        fname = os.path.relpath(fname)
        if fname in checked:
            return
        checked.add(fname)

        line = None
        with open(fname, "rb") as f:
            for n, line in enumerate(f, start=1):
                if crlf:
                    if b"\r" in line:
                        print(f"{fname}@{n}: CR found")
                        return
                if trail_white:
                    line = line[:-1]
                    if not crlf:
                        line = line.rstrip(b'\r')
                    if line.rstrip() != line:
                        print(f"{fname}@{n}: trailing white space found")
                        return

        if line is not None and not line.strip():
            print(f"{fname}: final blank line")

    def check_files(root, patterns, **kwargs):
        """Check a number of files for white space abuse."""
        for where, dirs, files in os.walk(root):
            for f in files:
                fname = os.path.join(where, f)
                for p in patterns:
                    if fnmatch.fnmatch(fname, p):
                        check_file(fname, **kwargs)
                        break
            for ignore_dir in ignore_dirs:
                ignored = []
                for dir_name in dirs:
                    if fnmatch.fnmatch(dir_name, ignore_dir):
                        ignored.append(dir_name)
                for dir_name in ignored:
                    dirs.remove(dir_name)

    check_files("coverage", ["*.py"])
    check_files("coverage/ctracer", ["*.c", "*.h"])
    check_files("coverage/htmlfiles", ["*.html", "*.scss", "*.css", "*.js"])
    check_files("tests", ["*.py"])
    check_files("tests", ["*,cover"], trail_white=False)
    check_files("tests/js", ["*.js", "*.html"])
    check_file("setup.py")
    check_file("igor.py")
    check_file("Makefile")
    check_files(".", ["*.rst", "*.txt"])
    check_files(".", ["*.pip"])
    check_files(".github", ["*"])
    check_files("ci", ["*"])


def print_banner(label):
    """Print the version of Python."""
    try:
        impl = platform.python_implementation()
    except AttributeError:
        impl = "Python"

    version = platform.python_version()

    if PYPY:
        version += " (pypy %s)" % ".".join(str(v) for v in sys.pypy_version_info)

    rev = platform.python_revision()
    if rev:
        version += f" (rev {rev})"

    try:
        which_python = os.path.relpath(sys.executable)
    except ValueError:
        # On Windows having a python executable on a different drive
        # than the sources cannot be relative.
        which_python = sys.executable
    print(f'=== {impl} {version} {label} ({which_python}) ===')
    sys.stdout.flush()


def do_quietly(command):
    """Run a command in a shell, and suppress all output."""
    proc = subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return proc.returncode


def get_release_facts():
    """Return an object with facts about the current release."""
    import coverage
    import coverage.version
    facts = types.SimpleNamespace()
    facts.ver = coverage.__version__
    facts.vi = coverage.version_info
    facts.dev = coverage.version._dev
    facts.shortver = f"{facts.vi[0]}.{facts.vi[1]}.{facts.vi[2]}"
    facts.anchor = facts.shortver.replace(".", "-")
    if facts.vi[3] != "final":
        facts.anchor += f"{facts.vi[3][0]}{facts.vi[4]}"
    facts.next_vi = (facts.vi[0], facts.vi[1], facts.vi[2]+1, "alpha", 0)
    facts.now = datetime.datetime.now()
    facts.branch = subprocess.getoutput("git rev-parse --abbrev-ref @")
    facts.sha = subprocess.getoutput("git rev-parse @")
    return facts


def update_file(fname, pattern, replacement):
    """Update the contents of a file, replacing pattern with replacement."""
    with open(fname) as fobj:
        old_text = fobj.read()

    new_text = re.sub(pattern, replacement, old_text, count=1)

    if new_text != old_text:
        print(f"Updating {fname}")
        with open(fname, "w") as fobj:
            fobj.write(new_text)

UNRELEASED = "Unreleased\n----------"

def do_edit_for_release():
    """Edit a few files in preparation for a release."""
    facts = get_release_facts()

    if facts.dev:
        print(f"**\n** This is a dev release: {facts.ver}\n**\n\nNo edits")
        return

    # NOTICE.txt
    update_file("NOTICE.txt", r"Copyright 2004.*? Ned", f"Copyright 2004-{facts.now:%Y} Ned")

    # CHANGES.rst
    title = f"Version {facts.ver} — {facts.now:%Y-%m-%d}"
    rule = "-" * len(title)
    new_head = f".. _changes_{facts.anchor}:\n\n{title}\n{rule}"

    update_file("CHANGES.rst", re.escape(UNRELEASED), new_head)

    # doc/conf.py
    new_conf = textwrap.dedent(f"""\
        # @@@ editable
        copyright = "2009\N{EN DASH}{facts.now:%Y}, Ned Batchelder" # pylint: disable=redefined-builtin
        # The short X.Y.Z version.
        version = "{facts.shortver}"
        # The full version, including alpha/beta/rc tags.
        release = "{facts.ver}"
        # The date of release, in "monthname day, year" format.
        release_date = "{facts.now:%B %-d, %Y}"
        # @@@ end
        """)
    update_file("doc/conf.py", r"(?s)# @@@ editable\n.*# @@@ end\n", new_conf)


def do_bump_version():
    """Edit a few files right after a release to bump the version."""
    facts = get_release_facts()

    # CHANGES.rst
    update_file(
        "CHANGES.rst",
        r"(?m)^\.\. _changes_",
        f"{UNRELEASED}\n\nNothing yet.\n\n\n.. _changes_",
    )

    # coverage/version.py
    next_version = f"version_info = {facts.next_vi}\n_dev = 1".replace("'", '"')
    update_file("coverage/version.py", r"(?m)^version_info = .*\n_dev = \d+$", next_version)


def do_cheats():
    """Show a cheatsheet of useful things during releasing."""
    facts = get_release_facts()
    pprint.pprint(facts.__dict__)
    print()
    print(f"Coverage version is {facts.ver}")

    egg = "egg=coverage==0.0"   # to force a re-install
    if facts.branch == "master":
        print(f"pip install git+https://github.com/nedbat/coveragepy#{egg}")
    else:
        print(f"pip install git+https://github.com/nedbat/coveragepy@{facts.branch}#{egg}")
    print(f"pip install git+https://github.com/nedbat/coveragepy@{facts.sha}#{egg}")
    print(f"https://coverage.readthedocs.io/en/{facts.ver}/changes.html#changes-{facts.anchor}")

    print(
        "\n## For GitHub commenting:\n" +
        "This is now released as part of " +
        f"[coverage {facts.ver}](https://pypi.org/project/coverage/{facts.ver})."
    )


def do_help():
    """List the available commands"""
    items = list(globals().items())
    items.sort()
    for name, value in items:
        if name.startswith('do_'):
            print(f"{name[3:]:<20}{value.__doc__}")


def analyze_args(function):
    """What kind of args does `function` expect?

    Returns:
        star, num_pos:
            star(boolean): Does `function` accept *args?
            num_args(int): How many positional arguments does `function` have?
    """
    argspec = inspect.getfullargspec(function)
    return bool(argspec.varargs), len(argspec.args)


def main(args):
    """Main command-line execution for igor.

    Verbs are taken from the command line, and extra words taken as directed
    by the arguments needed by the handler.

    """
    while args:
        verb = args.pop(0)
        handler = globals().get('do_'+verb)
        if handler is None:
            print(f"*** No handler for {verb!r}")
            return 1
        star, num_args = analyze_args(handler)
        if star:
            # Handler has *args, give it all the rest of the command line.
            handler_args = args
            args = []
        else:
            # Handler has specific arguments, give it only what it needs.
            handler_args = args[:num_args]
            args = args[num_args:]
        ret = handler(*handler_args)
        # If a handler returns a failure-like value, stop.
        if ret:
            return ret
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
