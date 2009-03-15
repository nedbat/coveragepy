"""Run tests in the farm subdirectory.  Requires nose."""

import filecmp, fnmatch, glob, os, shutil, sys
from coverage.files import FileLocator

try:
    import subprocess
except ImportError:
    subprocess = None


def test_farm(clean_only=False):
    """A test-generating function for nose to find and run."""
    for fname in glob.glob("test/farm/*/*.py"):
        case = FarmTestCase(fname, clean_only)
        yield (case.execute,)


class FarmTestCase(object):
    def __init__(self, runpy, clean_only=False, dont_clean=False):
        self.dir, self.runpy = os.path.split(runpy)
        self.clean_only = clean_only
        self.dont_clean = dont_clean

    def cd(self, newdir):
        cwd = os.getcwd()
        os.chdir(newdir)
        return cwd

    def execute(self):
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
                
        execfile(self.runpy, glo)

        self.cd(cwd)

    def fnmatch_list(self, files, filepattern):
        """Filter the list of `files` to only those that match `filepattern`.
        
        Returns a string naming the filtered files.
        
        """
        files = [f for f in files if fnmatch.fnmatch(f, filepattern)]
        return ", ".join(files)

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
        for cmd in cmds.split("\n"):
            if subprocess:
                proc = subprocess.Popen(cmd, shell=True, 
                          stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
                retcode = proc.wait()
                output = proc.stdout.read()
            else:
                stdin, stdouterr = os.popen4(cmd)
                output = stdouterr.read()
                retcode = 0 # Can't tell if the process failed.
            print output,
            if retcode:
                raise Exception("command exited abnormally")
        self.cd(cwd)

    def compare(self, dir1, dir2, filepattern=None):
        dc = filecmp.dircmp(dir1, dir2)
        diff_files = self.fnmatch_list(dc.diff_files, filepattern)
        left_only = self.fnmatch_list(dc.left_only, filepattern)
        right_only = self.fnmatch_list(dc.right_only, filepattern)
        assert not diff_files, "Files differ: %s" % (diff_files)
        assert not left_only, "Files in %s only: %s" % (dir1, left_only)
        assert not right_only, "Files in %s only: %s" % (dir2, right_only)

    def clean(self, cleandir):
        if os.path.exists(cleandir):
            shutil.rmtree(cleandir)


# So that we can run just one farm run.py at a time.
if __name__ == '__main__':
    op = sys.argv[1]
    if op == 'run':
        # Run the test for real.
        case = FarmTestCase(sys.argv[2])
        case.execute()
    if op == 'out':
        # Run the test, but don't clean up, so we can examine the output.
        case = FarmTestCase(sys.argv[2], dont_clean=True)
        case.execute()
    elif op == 'clean':
        # Run all the tests, but just clean.
        for test in test_farm(clean_only=True):
            test[0](*test[1:])
    else:
        print "Need an operation: run, out, clean"
