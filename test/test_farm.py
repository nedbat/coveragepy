"""Run tests in the farm subdirectory.  Designed for nose."""

import difflib, filecmp, fnmatch, glob, os, re, shutil, sys

sys.path.insert(0, os.path.split(__file__)[0]) # Force relative import for Py3k
from backtest import run_command, execfile # pylint: disable-msg=W0622


def test_farm(clean_only=False):
    """A test-generating function for nose to find and run."""
    for fname in glob.glob("test/farm/*/*.py"):
        case = FarmTestCase(fname, clean_only)
        yield (case,)


class FarmTestCase(object):
    """A test case from the farm tree.
    
    Tests are short Python script files, often called run.py:
    
        copy("src", "out")
        run('''
            coverage -x white.py
            coverage -a white.py
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

    def cd(self, newdir):
        """Change the current directory, and return the old one."""
        cwd = os.getcwd()
        os.chdir(newdir)
        return cwd

    def __call__(self):
        """Execute the test from the run.py file.
        
        """
        cwd = self.cd(self.dir)

        # Prepare a dictionary of globals for the run.py files to use.
        fns = "copy run runfunc compare contains doesnt_contain clean".split()
        if self.clean_only:
            glo = dict([(fn, self.noop) for fn in fns])
            glo['clean'] = self.clean
        else:
            glo = dict([(fn, getattr(self, fn)) for fn in fns])
            if self.dont_clean:
                glo['clean'] = self.noop
        
        try:
            execfile(self.runpy, glo)
        finally:
            self.cd(cwd)

    def run_fully(self):
        """Run as a full test case, with setUp and tearDown."""
        self.setUp()
        try:
            self()
        finally:
            self.tearDown()

    def fnmatch_list(self, files, filepattern):
        """Filter the list of `files` to only those that match `filepattern`.
        
        If `filepattern` is None, then return the entire list of files.
        
        Returns a list of the filtered files.
        
        """
        if filepattern:
            files = [f for f in files if fnmatch.fnmatch(f, filepattern)]
        return files

    def setUp(self):
        """Test set up, run by nose before __call__."""

        # Modules should be importable from the current directory.
        self.old_syspath = sys.path[:]
        sys.path.insert(0, '')
    
    def tearDown(self):
        """Test tear down, run by nose after __call__."""
        # Make sure no matter what, the test is cleaned up.
        if not self.dont_clean:
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
        try:
            for cmd in cmds.split("\n"):
                cmd = cmd.strip()
                if not cmd:
                    continue
                retcode, output = run_command(cmd)
                print(output.rstrip())
                if outfile:
                    open(outfile, "a+").write(output)
                if retcode:
                    raise Exception("command exited abnormally")
        finally:
            self.cd(cwd)

    def runfunc(self, fn, rundir="src"):
        """Run a function.
        
        `fn` is a callable.
        `rundir` is the directory in which to run the function.
        
        """
        
        cwd = self.cd(rundir)
        try:
            fn()
        finally:
            self.cd(cwd)

    def compare(self, dir1, dir2, filepattern=None, size_within=0,
            left_extra=False, right_extra=False, scrubs=None
            ):
        """Compare files matching `filepattern` in `dir1` and `dir2`.
        
        `dir2` is interpreted as a prefix, with Python version numbers appended
        to find the actual directory to compare with. "foo" will compare against
        "foo_v241", "foo_v24", "foo_v2", or "foo", depending on which directory
        is found first.
        
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
        diff_files = self.fnmatch_list(dc.diff_files, filepattern)
        left_only = self.fnmatch_list(dc.left_only, filepattern)
        right_only = self.fnmatch_list(dc.right_only, filepattern)
        
        if size_within:
            # The files were already compared, use the diff_files list as a
            # guide for size comparison.
            wrong_size = []
            for f in diff_files:
                left = open(os.path.join(dir1, f), "rb").read()
                right = open(os.path.join(dir2, f), "rb").read()
                size_l, size_r = len(left), len(right)
                big, little = max(size_l, size_r), min(size_l, size_r)
                if (big - little) / float(little) > size_within/100.0:
                    # print "%d %d" % (big, little)
                    # print "Left: ---\n%s\n-----\n%s" % (left, right)
                    wrong_size.append(f)
            assert not wrong_size, "File sizes differ: %s" % wrong_size
        else:
            # filecmp only compares in binary mode, but we want text mode.  So
            # look through the list of different files, and compare them
            # ourselves.
            text_diff = []
            for f in diff_files:
                left = open(os.path.join(dir1, f), "r").readlines()
                right = open(os.path.join(dir2, f), "r").readlines()
                if scrubs:
                    left = self._scrub(left, scrubs)
                    right = self._scrub(right, scrubs)
                if left != right:
                    text_diff.append(f)
                    print("".join(list(difflib.Differ().compare(left, right))))
            assert not text_diff, "Files differ: %s" % text_diff

        if not left_extra:
            assert not left_only, "Files in %s only: %s" % (dir1, left_only)
        if not right_extra:
            assert not right_only, "Files in %s only: %s" % (dir2, right_only)

    def _scrub(self, strlist, scrubs):
        """Scrub uninteresting data from the strings in `strlist`.
        
        `scrubs is a list of (find, replace) pairs of regexes that are used on
        each string in `strlist`.  A list of scrubbed strings is returned.
        
        """
        scrubbed = []
        for s in strlist:
            for rgx_find, rgx_replace in scrubs:
                s = re.sub(rgx_find, rgx_replace, s)
            scrubbed.append(s)
        return scrubbed

    def contains(self, filename, *strlist):
        """Check that the file contains all of a list of strings.
        
        An assert will be raised if one of the arguments in `strlist` is
        missing in `filename`.
        
        """
        text = open(filename, "r").read()
        for s in strlist:
            assert s in text, "Missing content in %s: %r" % (filename, s)

    def doesnt_contain(self, filename, *strlist):
        """Check that the file contains none of a list of strings.
        
        An assert will be raised if any of the strings in strlist appears in
        `filename`.
        
        """
        text = open(filename, "r").read()
        for s in strlist:
            assert s not in text, "Forbidden content in %s: %r" % (filename, s)

    def clean(self, cleandir):
        """Clean `cleandir` by removing it and all its children completely."""
        if os.path.exists(cleandir):
            shutil.rmtree(cleandir)

def main():
    """Command-line access to test_farm.
    
    Commands:
    
    run testcase    - Run a single test case.
    out testcase    - Run a test case, but don't clean up, to see the output.
    clean           - Clean all the output for all tests.
        
    """
    op = sys.argv[1]
    if op == 'run':
        # Run the test for real.
        case = FarmTestCase(sys.argv[2])
        case.run_fully()
    elif op == 'out':
        # Run the test, but don't clean up, so we can examine the output.
        case = FarmTestCase(sys.argv[2], dont_clean=True)
        case.run_fully()
    elif op == 'clean':
        # Run all the tests, but just clean.
        for test in test_farm(clean_only=True):
            test[0].run_fully()
    else:
        print("Need an operation: run, out, clean")
    
# So that we can run just one farm run.py at a time.
if __name__ == '__main__':
    main()
