"""Run tests in the farm subdirectory.  Designed for nose."""

import difflib, filecmp, fnmatch, glob, os, re, shutil, sys
from nose.plugins.skip import SkipTest

from tests.backtest import run_command, execfile      # pylint: disable=W0622

from coverage.control import _TEST_NAME_FILE


def test_farm(clean_only=False):
    """A test-generating function for nose to find and run."""
    for fname in glob.glob("tests/farm/*/*.py"):
        case = FarmTestCase(fname, clean_only)
        yield (case,)


# "rU" was deprecated in 3.4
READ_MODE = "rU" if sys.version_info < (3, 4) else "r"


class FarmTestCase(object):
    """A test case from the farm tree.

    Tests are short Python script files, often called run.py:

        copy("src", "out")
        run('''
            coverage run white.py
            coverage annotate white.py
            ''', rundir="out")
        compare("out", "gold", "*,cover")
        clean("out")

    Verbs (copy, run, compare, clean) are methods in this class.  FarmTestCase
    has options to allow various uses of the test cases (normal execution,
    cleaning-only, or run and leave the results for debugging).

    """
    def __init__(self, runpy, clean_only=False, dont_clean=False):
        """Create a test case from a run.py file.

        `clean_only` means that only the clean() action is executed.
        `dont_clean` means that the clean() action is not executed.

        """
        self.description = runpy
        self.dir, self.runpy = os.path.split(runpy)
        self.clean_only = clean_only
        self.dont_clean = dont_clean
        self.ok = True

    def cd(self, newdir):
        """Change the current directory, and return the old one."""
        cwd = os.getcwd()
        os.chdir(newdir)
        return cwd

    def addtopath(self, directory):
        """Add `directory` to the path, and return the old path."""
        oldpath = sys.path[:]
        if directory is not None:
            sys.path.insert(0, directory)
        return oldpath

    def restorepath(self, path):
        """Restore the system path to `path`."""
        sys.path = path

    def __call__(self):
        """Execute the test from the run.py file.

        """
        if _TEST_NAME_FILE:                                 # pragma: debugging
            with open(_TEST_NAME_FILE, "w") as f:
                f.write(self.description.replace("/", "_"))

        cwd = self.cd(self.dir)

        # Prepare a dictionary of globals for the run.py files to use.
        fns = """
            copy run runfunc clean skip
            compare contains contains_any doesnt_contain
            """.split()
        if self.clean_only:
            glo = dict((fn, self.noop) for fn in fns)
            glo['clean'] = self.clean
        else:
            glo = dict((fn, getattr(self, fn)) for fn in fns)
            if self.dont_clean:                 # pragma: not covered
                glo['clean'] = self.noop

        old_mods = dict(sys.modules)
        try:
            execfile(self.runpy, glo)
        except Exception:
            self.ok = False
            raise
        finally:
            self.cd(cwd)
            # Remove any new modules imported during the test run. This lets us
            # import the same source files for more than one test.
            to_del = [m for m in sys.modules if m not in old_mods]
            for m in to_del:
                del sys.modules[m]

    def run_fully(self):        # pragma: not covered
        """Run as a full test case, with setUp and tearDown."""
        self.setUp()
        try:
            self()
        finally:
            self.tearDown()

    def fnmatch_list(self, files, file_pattern):
        """Filter the list of `files` to only those that match `file_pattern`.

        If `file_pattern` is None, then return the entire list of files.

        Returns a list of the filtered files.

        """
        if file_pattern:
            files = [f for f in files if fnmatch.fnmatch(f, file_pattern)]
        return files

    def setUp(self):
        """Test set up, run by nose before __call__."""

        # Modules should be importable from the current directory.
        self.old_syspath = sys.path[:]
        sys.path.insert(0, '')

    def tearDown(self):
        """Test tear down, run by nose after __call__."""
        # Make sure the test is cleaned up, unless we never want to, or if the
        # test failed.
        if not self.dont_clean and self.ok:         # pragma: part covered
            self.clean_only = True
            self()

        # Restore the original sys.path
        sys.path = self.old_syspath

    # Functions usable inside farm run.py files

    def noop(self, *args, **kwargs):
        """A no-op function to stub out run, copy, etc, when only cleaning."""
        pass

    def copy(self, src, dst):
        """Copy a directory."""

        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)

    def run(self, cmds, rundir="src", outfile=None):
        """Run a list of commands.

        `cmds` is a string, commands separated by newlines.
        `rundir` is the directory in which to run the commands.
        `outfile` is a filename to redirect stdout to.

        """
        cwd = self.cd(rundir)
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
                    raise Exception("command exited abnormally")
        finally:
            if outfile:
                fout.close()
            self.cd(cwd)

    def runfunc(self, fn, rundir="src", addtopath=None):
        """Run a function.

        `fn` is a callable.
        `rundir` is the directory in which to run the function.

        """

        cwd = self.cd(rundir)
        oldpath = self.addtopath(addtopath)
        try:
            fn()
        finally:
            self.cd(cwd)
            self.restorepath(oldpath)

    def compare(self, dir1, dir2, file_pattern=None, size_within=0,
            left_extra=False, right_extra=False, scrubs=None
            ):
        """Compare files matching `file_pattern` in `dir1` and `dir2`.

        `dir2` is interpreted as a prefix, with Python version numbers appended
        to find the actual directory to compare with. "foo" will compare
        against "foo_v241", "foo_v24", "foo_v2", or "foo", depending on which
        directory is found first.

        `size_within` is a percentage delta for the file sizes.  If non-zero,
        then the file contents are not compared (since they are expected to
        often be different), but the file sizes must be within this amount.
        For example, size_within=10 means that the two files' sizes must be
        within 10 percent of each other to compare equal.

        `left_extra` true means the left directory can have extra files in it
        without triggering an assertion.  `right_extra` means the right
        directory can.

        `scrubs` is a list of pairs, regex find and replace patterns to use to
        scrub the files of unimportant differences.

        An assertion will be raised if the directories fail one of their
        matches.

        """
        # Search for a dir2 with a version suffix.
        version_suff = ''.join(map(str, sys.version_info[:3]))
        while version_suff:
            trydir = dir2 + '_v' + version_suff
            if os.path.exists(trydir):
                dir2 = trydir
                break
            version_suff = version_suff[:-1]

        assert os.path.exists(dir1), "Left directory missing: %s" % dir1
        assert os.path.exists(dir2), "Right directory missing: %s" % dir2

        dc = filecmp.dircmp(dir1, dir2)
        diff_files = self.fnmatch_list(dc.diff_files, file_pattern)
        left_only = self.fnmatch_list(dc.left_only, file_pattern)
        right_only = self.fnmatch_list(dc.right_only, file_pattern)
        show_diff = True

        if size_within:
            # The files were already compared, use the diff_files list as a
            # guide for size comparison.
            wrong_size = []
            for f in diff_files:
                with open(os.path.join(dir1, f), "rb") as fobj:
                    left = fobj.read()
                with open(os.path.join(dir2, f), "rb") as fobj:
                    right = fobj.read()
                size_l, size_r = len(left), len(right)
                big, little = max(size_l, size_r), min(size_l, size_r)
                if (big - little) / float(little) > size_within/100.0:
                    # print "%d %d" % (big, little)
                    # print "Left: ---\n%s\n-----\n%s" % (left, right)
                    wrong_size.append("%s (%s,%s)" % (f, size_l, size_r))
            assert not wrong_size, (
                "File sizes differ between %s and %s: %s" % (
                    dir1, dir2, ", ".join(wrong_size)
                ))

            # We'll show the diff if the files differed enough in size.
            show_diff = bool(wrong_size)

        if show_diff:
            # filecmp only compares in binary mode, but we want text mode.  So
            # look through the list of different files, and compare them
            # ourselves.
            text_diff = []
            for f in diff_files:
                with open(os.path.join(dir1, f), READ_MODE) as fobj:
                    left = fobj.read()
                with open(os.path.join(dir2, f), READ_MODE) as fobj:
                    right = fobj.read()
                if scrubs:
                    left = self._scrub(left, scrubs)
                    right = self._scrub(right, scrubs)
                if left != right:
                    text_diff.append(f)
                    left = left.splitlines()
                    right = right.splitlines()
                    print("\n".join(difflib.Differ().compare(left, right)))
            assert not text_diff, "Files differ: %s" % text_diff

        if not left_extra:
            assert not left_only, "Files in %s only: %s" % (dir1, left_only)
        if not right_extra:
            assert not right_only, "Files in %s only: %s" % (dir2, right_only)

    def _scrub(self, strdata, scrubs):
        """Scrub uninteresting data from the payload in `strdata`.

        `scrubs` is a list of (find, replace) pairs of regexes that are used on
        `strdata`.  A string is returned.

        """
        for rgx_find, rgx_replace in scrubs:
            strdata = re.sub(rgx_find, rgx_replace, strdata)
        return strdata

    def contains(self, filename, *strlist):
        """Check that the file contains all of a list of strings.

        An assert will be raised if one of the arguments in `strlist` is
        missing in `filename`.

        """
        with open(filename, "r") as fobj:
            text = fobj.read()
        for s in strlist:
            assert s in text, "Missing content in %s: %r" % (filename, s)

    def contains_any(self, filename, *strlist):
        """Check that the file contains at least one of a list of strings.

        An assert will be raised if none of the arguments in `strlist` is in
        `filename`.

        """
        with open(filename, "r") as fobj:
            text = fobj.read()
        for s in strlist:
            if s in text:
                return
        assert False, "Missing content in %s: %r [1 of %d]" % (
            filename, strlist[0], len(strlist),
        )

    def doesnt_contain(self, filename, *strlist):
        """Check that the file contains none of a list of strings.

        An assert will be raised if any of the strings in strlist appears in
        `filename`.

        """
        with open(filename, "r") as fobj:
            text = fobj.read()
        for s in strlist:
            assert s not in text, "Forbidden content in %s: %r" % (filename, s)

    def clean(self, cleandir):
        """Clean `cleandir` by removing it and all its children completely."""
        # rmtree gives mysterious failures on Win7, so retry a "few" times.
        # I've seen it take over 100 tries, so, 1000!  This is probably the
        # most unpleasant hack I've written in a long time...
        tries = 1000
        while tries:                    # pragma: part covered
            if os.path.exists(cleandir):
                try:
                    shutil.rmtree(cleandir)
                except OSError:         # pragma: not covered
                    if tries == 1:
                        raise
                    else:
                        tries -= 1
                        continue
            break

    def skip(self, msg=None):
        """Skip the current test."""
        raise SkipTest(msg)


def main():     # pragma: not covered
    """Command-line access to test_farm.

    Commands:

    run testcase ...    - Run specific test case(s)
    out testcase ...    - Run test cases, but don't clean up, leaving output.
    clean               - Clean all the output for all tests.

    """
    op = 'help'
    try:
        op = sys.argv[1]
    except IndexError:
        pass

    if op == 'run':
        # Run the test for real.
        for test_case in sys.argv[2:]:
            case = FarmTestCase(test_case)
            case.run_fully()
    elif op == 'out':
        # Run the test, but don't clean up, so we can examine the output.
        for test_case in sys.argv[2:]:
            case = FarmTestCase(test_case, dont_clean=True)
            case.run_fully()
    elif op == 'clean':
        # Run all the tests, but just clean.
        for test in test_farm(clean_only=True):
            test[0].run_fully()
    else:
        print(main.__doc__)

# So that we can run just one farm run.py at a time.
if __name__ == '__main__':
    main()
