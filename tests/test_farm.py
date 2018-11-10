# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Run tests in the farm sub-directory.  Designed for pytest."""

import difflib
import filecmp
import fnmatch
import glob
import os
import re
import shutil
import sys

import pytest

from unittest_mixins import ModuleAwareMixin, SysPathAwareMixin, change_dir
from tests.helpers import run_command
from tests.backtest import execfile         # pylint: disable=redefined-builtin

from coverage import env
from coverage.backunittest import unittest


# Look for files that become tests.
TEST_FILES = glob.glob("tests/farm/*/*.py")


@pytest.mark.parametrize("filename", TEST_FILES)
def test_farm(filename):
    if env.JYTHON:
        # All of the farm tests use reporting, so skip them all.
        skip("Farm tests don't run on Jython")
    FarmTestCase(filename).run_fully()


# "rU" was deprecated in 3.4
READ_MODE = "rU" if env.PYVERSION < (3, 4) else "r"


class FarmTestCase(ModuleAwareMixin, SysPathAwareMixin, unittest.TestCase):
    """A test case from the farm tree.

    Tests are short Python script files, often called run.py:

        copy("src", "out")
        run('''
            coverage run white.py
            coverage annotate white.py
            ''', rundir="out")
        compare("gold", "out", "*,cover")
        clean("out")

    Verbs (copy, run, compare, clean) are methods in this class.  FarmTestCase
    has options to allow various uses of the test cases (normal execution,
    cleaning-only, or run and leave the results for debugging).

    This class is a unittest.TestCase so that we can use behavior-modifying
    mixins, but it's only useful as a test function.  Yes, this is confusing.

    """

    # We don't want test runners finding this and instantiating it themselves.
    __test__ = False

    def __init__(self, runpy, clean_only=False, dont_clean=False):
        """Create a test case from a run.py file.

        `clean_only` means that only the clean() action is executed.
        `dont_clean` means that the clean() action is not executed.

        """
        super(FarmTestCase, self).__init__()

        self.description = runpy
        self.dir, self.runpy = os.path.split(runpy)
        self.clean_only = clean_only
        self.dont_clean = dont_clean
        self.ok = True

    def setUp(self):
        """Test set up, run by the test runner before __call__."""
        super(FarmTestCase, self).setUp()
        # Modules should be importable from the current directory.
        sys.path.insert(0, '')

    def tearDown(self):
        """Test tear down, run by the test runner after __call__."""
        # Make sure the test is cleaned up, unless we never want to, or if the
        # test failed.
        if not self.dont_clean and self.ok:             # pragma: part covered
            self.clean_only = True
            self()

        super(FarmTestCase, self).tearDown()

        # This object will be run via the __call__ method, and test runners
        # don't do cleanups in that case.  Do them now.
        self.doCleanups()

    def runTest(self):                                  # pragma: not covered
        """Here to make unittest.TestCase happy, but will never be invoked."""
        raise Exception("runTest isn't used in this class!")

    def __call__(self):                                 # pylint: disable=arguments-differ
        """Execute the test from the runpy file."""
        # Prepare a dictionary of globals for the run.py files to use.
        fns = """
            copy run clean skip
            compare contains contains_any doesnt_contain
            """.split()
        if self.clean_only:
            glo = dict((fn, noop) for fn in fns)
            glo['clean'] = clean
        else:
            glo = dict((fn, globals()[fn]) for fn in fns)
            if self.dont_clean:                 # pragma: debugging
                glo['clean'] = noop

        with change_dir(self.dir):
            try:
                execfile(self.runpy, glo)
            except Exception:
                self.ok = False
                raise

    def run_fully(self):
        """Run as a full test case, with setUp and tearDown."""
        self.setUp()
        try:
            self()
        finally:
            self.tearDown()


# Functions usable inside farm run.py files

def noop(*args_unused, **kwargs_unused):
    """A no-op function to stub out run, copy, etc, when only cleaning."""
    pass


def copy(src, dst):
    """Copy a directory."""
    if os.path.exists(dst):
        pytest.fail('%s already exists.' % os.path.join(os.getcwd(), dst))  # pragma: only failure
    shutil.copytree(src, dst)


def run(cmds, rundir="src", outfile=None):
    """Run a list of commands.

    `cmds` is a string, commands separated by newlines.
    `rundir` is the directory in which to run the commands.
    `outfile` is a file name to redirect stdout to.

    """
    with change_dir(rundir):
        if outfile:
            fout = open(outfile, "a+")
        try:
            for cmd in cmds.split("\n"):
                cmd = cmd.strip()
                if not cmd:
                    continue
                retcode, output = run_command(cmd)
                print(output.rstrip())
                if outfile:
                    fout.write(output)
                if retcode:
                    raise Exception("command exited abnormally")    # pragma: only failure
        finally:
            if outfile:
                fout.close()


def versioned_directory(d):
    """Find a subdirectory of d specific to the Python version.

    For example, on Python 3.6.4 rc 1, it returns the first of these
    directories that exists::

        d/3.6.4.candidate.1
        d/3.6.4.candidate
        d/3.6.4
        d/3.6
        d/3
        d

    Returns: a string, the path to an existing directory.

    """
    ver_parts = list(map(str, sys.version_info))
    for nparts in range(len(ver_parts), -1, -1):
        version = ".".join(ver_parts[:nparts])
        subdir = os.path.join(d, version)
        if os.path.exists(subdir):
            return subdir
    raise Exception("Directory missing: {}".format(d))                  # pragma: only failure


def compare(
        expected_dir, actual_dir, file_pattern=None, size_within=0,
        actual_extra=False, scrubs=None,
        ):
    """Compare files matching `file_pattern` in `expected_dir` and `actual_dir`.

    A version-specific subdirectory of `expected_dir` will be used if
    it exists.

    `size_within` is a percentage delta for the file sizes.  If non-zero,
    then the file contents are not compared (since they are expected to
    often be different), but the file sizes must be within this amount.
    For example, size_within=10 means that the two files' sizes must be
    within 10 percent of each other to compare equal.

    `actual_extra` true means `actual_dir` can have extra files in it
    without triggering an assertion.

    `scrubs` is a list of pairs: regexes to find and replace to scrub the
    files of unimportant differences.

    An assertion will be raised if the directories fail one of their
    matches.

    """
    expected_dir = versioned_directory(expected_dir)

    dc = filecmp.dircmp(expected_dir, actual_dir)
    diff_files = fnmatch_list(dc.diff_files, file_pattern)
    expected_only = fnmatch_list(dc.left_only, file_pattern)
    actual_only = fnmatch_list(dc.right_only, file_pattern)
    show_diff = True

    if size_within:
        # The files were already compared, use the diff_files list as a
        # guide for size comparison.
        wrong_size = []
        for f in diff_files:
            with open(os.path.join(expected_dir, f), "rb") as fobj:
                expected = fobj.read()
            with open(os.path.join(actual_dir, f), "rb") as fobj:
                actual = fobj.read()
            size_e, size_a = len(expected), len(actual)
            big, little = max(size_e, size_a), min(size_e, size_a)
            if (big - little) / float(little) > size_within/100.0:
                # print "%d %d" % (big, little)
                # print "expected: ---\n%s\n-----\n%s" % (expected, actual)
                wrong_size.append("%s (%s,%s)" % (f, size_e, size_a))   # pragma: only failure
        if wrong_size:
            print("File sizes differ between %s and %s: %s" % (         # pragma: only failure
                expected_dir, actual_dir, ", ".join(wrong_size)
            ))

        # We'll show the diff iff the files differed enough in size.
        show_diff = bool(wrong_size)

    if show_diff:
        # filecmp only compares in binary mode, but we want text mode.  So
        # look through the list of different files, and compare them
        # ourselves.
        text_diff = []
        for f in diff_files:
            expected_file = os.path.join(expected_dir, f)
            actual_file = os.path.join(actual_dir, f)
            with open(expected_file, READ_MODE) as fobj:
                expected = fobj.read()
            with open(actual_file, READ_MODE) as fobj:
                actual = fobj.read()
            if scrubs:
                expected = scrub(expected, scrubs)
                actual = scrub(actual, scrubs)
            if expected != actual:                              # pragma: only failure
                text_diff.append('%s != %s' % (expected_file, actual_file))
                expected = expected.splitlines()
                actual = actual.splitlines()
                print(":::: diff {!r} and {!r}".format(expected_file, actual_file))
                print("\n".join(difflib.Differ().compare(expected, actual)))
                print(":::: end diff {!r} and {!r}".format(expected_file, actual_file))
        assert not text_diff, "Files differ: %s" % '\n'.join(text_diff)

    assert not expected_only, "Files in %s only: %s" % (expected_dir, expected_only)
    if not actual_extra:
        assert not actual_only, "Files in %s only: %s" % (actual_dir, actual_only)


def contains(filename, *strlist):
    """Check that the file contains all of a list of strings.

    An assert will be raised if one of the arguments in `strlist` is
    missing in `filename`.

    """
    with open(filename, "r") as fobj:
        text = fobj.read()
    for s in strlist:
        assert s in text, "Missing content in %s: %r" % (filename, s)


def contains_any(filename, *strlist):
    """Check that the file contains at least one of a list of strings.

    An assert will be raised if none of the arguments in `strlist` is in
    `filename`.

    """
    with open(filename, "r") as fobj:
        text = fobj.read()
    for s in strlist:
        if s in text:
            return

    assert False, (                         # pragma: only failure
        "Missing content in %s: %r [1 of %d]" % (filename, strlist[0], len(strlist),)
    )


def doesnt_contain(filename, *strlist):
    """Check that the file contains none of a list of strings.

    An assert will be raised if any of the strings in `strlist` appears in
    `filename`.

    """
    with open(filename, "r") as fobj:
        text = fobj.read()
    for s in strlist:
        assert s not in text, "Forbidden content in %s: %r" % (filename, s)


def clean(cleandir):
    """Clean `cleandir` by removing it and all its children completely."""
    # rmtree gives mysterious failures on Win7, so retry a "few" times.
    # I've seen it take over 100 tries, so, 1000!  This is probably the
    # most unpleasant hack I've written in a long time...
    tries = 1000
    while tries:                    # pragma: part covered
        if os.path.exists(cleandir):
            try:
                shutil.rmtree(cleandir)
            except OSError:         # pragma: cant happen
                if tries == 1:
                    raise
                else:
                    tries -= 1
                    continue
        break


def skip(msg=None):
    """Skip the current test."""
    raise unittest.SkipTest(msg)


# Helpers

def fnmatch_list(files, file_pattern):
    """Filter the list of `files` to only those that match `file_pattern`.

    If `file_pattern` is None, then return the entire list of files.

    Returns a list of the filtered files.

    """
    if file_pattern:
        files = [f for f in files if fnmatch.fnmatch(f, file_pattern)]
    return files


def scrub(strdata, scrubs):
    """Scrub uninteresting data from the payload in `strdata`.

    `scrubs` is a list of (find, replace) pairs of regexes that are used on
    `strdata`.  A string is returned.

    """
    for rgx_find, rgx_replace in scrubs:
        strdata = re.sub(rgx_find, rgx_replace, strdata)
    return strdata


def main():     # pragma: debugging
    """Command-line access to farm tests.

    Commands:

    run testcase ...    - Run specific test case(s)
    out testcase ...    - Run test cases, but don't clean up, leaving output.
    clean               - Clean all the output for all tests.

    """
    try:
        op = sys.argv[1]
    except IndexError:
        op = 'help'

    if op == 'run':
        # Run the test for real.
        for filename in sys.argv[2:]:
            FarmTestCase(filename).run_fully()
    elif op == 'out':
        # Run the test, but don't clean up, so we can examine the output.
        for filename in sys.argv[2:]:
            FarmTestCase(filename, dont_clean=True).run_fully()
    elif op == 'clean':
        # Run all the tests, but just clean.
        for filename in TEST_FILES:
            FarmTestCase(filename, clean_only=True).run_fully()
    else:
        print(main.__doc__)

# So that we can run just one farm run.py at a time.
if __name__ == '__main__':          # pragma: debugging
    main()
