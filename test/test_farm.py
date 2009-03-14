"""Run tests in the farm subdirectory.  Requires nose."""

import filecmp, fnmatch, glob, os, shutil, sys
from coverage.files import FileLocator


def test_farm():
    """A test-generating function for nose to find and run."""
    for fname in glob.glob("test/farm/*/*.py"):
        case = FarmTestCase(fname)
        yield (case.execute,)

   
class FarmTestCase(object):
    def __init__(self, runpy):
        self.dir, self.runpy = os.path.split(runpy)
        
    def cd(self, newdir):
        cwd = os.getcwd()
        os.chdir(newdir)
        return cwd

    def execute(self):
        print "Running", self.runpy, "in", self.dir
        cwd = self.cd(self.dir)

        glo = dict([(a, getattr(self, a)) for a in "run compare clean".split()])
        execfile(self.runpy, glo)

        self.cd(cwd)

    def fnmatch_list(self, files, filepattern):
        """Filter the list of `files` to only those that match `filepattern`."""
        
        return [f for f in files if fnmatch.fnmatch(f, filepattern)]

    # Functions usable inside farm run.py files
    
    def run(self, cmds, rundir="src"):
        """Run a list of commands.
        
        `cmds` is a string, commands separated by newlines.
        `rundir` is the directory in which to run the commands.
        
        """
        cwd = self.cd(rundir)
        for cmd in cmds.split("\n"):
            stdin, stdouterr = os.popen4(cmd)
            output = stdouterr.read()
            print output,
        self.cd(cwd)

    def compare(self, dir1, dir2, filepattern=None):
        dc = filecmp.dircmp(dir1, dir2)
        
        pass

    def clean(self, cleandir):
        shutil.rmtree(cleandir)


# So that we can run just one farm run.py at a time.
if __name__ == '__main__':
    case = FarmTestCase(sys.argv[1])
    case.execute()
