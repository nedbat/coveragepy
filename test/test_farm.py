"""Run tests in the farm subdirectory.  Designed for nose."""

import filecmp, fnmatch, glob, os, shutil, sys

try:
    import subprocess
except ImportError:
    subprocess = None


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
        fns = "copy run compare clean".split()
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

    def fnmatch_list(self, files, filepattern):
        """Filter the list of `files` to only those that match `filepattern`.
        
        Returns a string naming the filtered files.
        
        """
        files = [f for f in files if fnmatch.fnmatch(f, filepattern)]
        return ", ".join(files)

    def setUp(self):
        """Test set up, run by nose before __call__."""
        pass
    
    def tearDown(self):
        """Test tear down, run by nose after __call__."""
        # Make sure no matter what, the test is cleaned up.
        self.clean_only = True
        self()

    # Functions usable inside farm run.py files
    
    def noop(self, *args, **kwargs):
        """A no-op function to stub out run, copy, etc, when only cleaning."""
        pass
    
    def copy(self, src, dst):
        """Copy a directory."""

        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)

    def run(self, cmds, rundir="src"):
        """Run a list of commands.
        
        `cmds` is a string, commands separated by newlines.
        `rundir` is the directory in which to run the commands.
        
        """
        cwd = self.cd(rundir)
        try:
            for cmd in cmds.split("\n"):
                if subprocess:
                    proc = subprocess.Popen(cmd, shell=True, 
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)
                    retcode = proc.wait()
                    output = proc.stdout.read()
                else:
                    _, stdouterr = os.popen4(cmd)
                    output = stdouterr.read()
                    retcode = 0 # Can't tell if the process failed.
                print output,
                if retcode:
                    raise Exception("command exited abnormally")
        finally:
            self.cd(cwd)

    def compare(self, dir1, dir2, filepattern=None, left_extra=False,
        right_extra=False
        ):
        """Compare files matching `filepattern` in `dir1` and `dir2`.
        
        `dir2` is interpreted as a prefix, with Python version numbers appended
        to find the actual directory to compare with. "foo" will compare against
        "foo_v241", "foo_v24", "foo_v2", or "foo", depending on which directory
        is found first.
        
        `left_extra` true means the left directory can have extra files in it
        without triggering an assertion.  `right_extra` means the right
        directory can.
        
        An assertion will be raised if the directories don't match in some way.
        
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
        
        assert not diff_files, "Files differ: %s" % (diff_files)
        if not left_extra:
            assert not left_only, "Files in %s only: %s" % (dir1, left_only)
        if not right_extra:
            assert not right_only, "Files in %s only: %s" % (dir2, right_only)

    def clean(self, cleandir):
        """Clean `cleandir` by removing it and all its children completely."""
        if os.path.exists(cleandir):
            shutil.rmtree(cleandir)

def main():
    op = sys.argv[1]
    if op == 'run':
        # Run the test for real.
        case = FarmTestCase(sys.argv[2])
        case()
    elif op == 'out':
        # Run the test, but don't clean up, so we can examine the output.
        case = FarmTestCase(sys.argv[2], dont_clean=True)
        case()
    elif op == 'clean':
        # Run all the tests, but just clean.
        for test in test_farm(clean_only=True):
            test[0](*test[1:])
    else:
        print "Need an operation: run, out, clean"
    
# So that we can run just one farm run.py at a time.
if __name__ == '__main__':
    main()
