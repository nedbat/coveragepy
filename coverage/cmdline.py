"""Command-line support for coverage.py"""

import getopt, sys

from coverage.annotate import AnnotateReporter
from coverage.summary import SummaryReporter
from coverage.execfile import run_python_file

USAGE = r"""
Coverage version %(__version__)s

Usage:

coverage -x [-p] MODULE.py [ARG1 ARG2 ...]
    Execute module, passing the given command-line arguments, collecting
    coverage data. With the -p option, write to a temporary file containing
    the machine name and process ID.

coverage -e
    Erase collected coverage data.

coverage -c
    Combine data from multiple coverage files (as created by -p option above)
    and store it into a single file representing the union of the coverage.

coverage -r [-m] [-i] [-o DIR,...] [FILE1 FILE2 ...]
    Report on the statement coverage for the given files.  With the -m
    option, show line numbers of the statements that weren't executed.

coverage -a [-d DIR] [-i] [-o DIR,...] [FILE1 FILE2 ...]
    Make annotated copies of the given files, marking statements that
    are executed with > and statements that are missed with !.  With
    the -d option, make the copies in that directory.  Without the -d
    option, make each copy in the same directory as the original.

-h  Print this help.

-i  Ignore errors while reporting or annotating.

-o DIR,...
    Omit reporting or annotating files when their filename path starts with
    a directory listed in the omit list.
    e.g. coverage -i -r -o c:\python25,lib\enthought\traits

Coverage data is saved in the file .coverage by default.  Set the
COVERAGE_FILE environment variable to save it somewhere else.
""".strip()


class CoverageScript:
    def __init__(self):
        import coverage
        self.covpkg = coverage
        self.coverage = coverage.coverage()

    def help(self, error=None):     #pragma: no cover
        if error:
            print error
            print
        print USAGE % self.covpkg.__dict__

    def command_line(self, argv, help_fn=None):
        # Collect the command-line options.
        help_fn = help_fn or self.help
        OK, ERR = 0, 1
        settings = {}
        optmap = {
            '-a': 'annotate',
            '-c': 'combine',
            '-d:': 'directory=',
            '-e': 'erase',
            '-h': 'help',
            '-i': 'ignore-errors',
            '-m': 'show-missing',
            '-p': 'parallel-mode',
            '-r': 'report',
            '-x': 'execute',
            '-o:': 'omit=',
            }
        short_opts = ''.join(map(lambda o: o[1:], optmap.keys()))
        long_opts = optmap.values()
        options, args = getopt.getopt(argv, short_opts, long_opts)
        for o, a in options:
            if optmap.has_key(o):
                settings[optmap[o]] = True
            elif optmap.has_key(o + ':'):
                settings[optmap[o + ':']] = a
            elif o[2:] in long_opts:
                settings[o[2:]] = True
            elif o[2:] + '=' in long_opts:
                settings[o[2:]+'='] = a

        if settings.get('help'):
            help_fn()
            return OK

        # Check for conflicts and problems in the options.
        for i in ['erase', 'execute']:
            for j in ['annotate', 'report', 'combine']:
                if settings.get(i) and settings.get(j):
                    help_fn("You can't specify the '%s' and '%s' "
                              "options at the same time." % (i, j))
                    return ERR

        args_needed = (settings.get('execute')
                       or settings.get('annotate')
                       or settings.get('report'))
        action = (settings.get('erase') 
                  or settings.get('combine')
                  or args_needed)
        if not action:
            help_fn("You must specify at least one of -e, -x, -c, -r, or -a.")
            return ERR
        if not args_needed and args:
            help_fn("Unexpected arguments: %s" % " ".join(args))
            return ERR
        
        # Do something.
        self.coverage.parallel_mode = settings.get('parallel-mode')
        self.coverage.get_ready()

        if settings.get('erase'):
            self.coverage.erase()
        
        if settings.get('execute'):
            if not args:
                help_fn("Nothing to do.")
                return ERR
            # Create the runtime environment the script on the cmdline expects.
            sys.argv = args
            self.coverage.start()
            run_python_file(sys.argv[0])
            self.coverage.stop()
        
        if settings.get('combine'):
            self.coverage.combine()

        ignore_errors = settings.get('ignore-errors')
        show_missing = settings.get('show-missing')
        directory = settings.get('directory=')

        omit = settings.get('omit=')
        if omit:
            omit = omit.split(',')
        
        if settings.get('report'):
            reporter = SummaryReporter(self.coverage, show_missing, ignore_errors)
            reporter.report(args, omit_prefixes=omit)
        if settings.get('annotate'):
            reporter = AnnotateReporter(self.coverage, ignore_errors)
            reporter.report(args, directory, omit_prefixes=omit)
        
        return OK
    
# Main entrypoint.  This is installed as the script entrypoint, so don't
# refactor it away...
def main():
    return CoverageScript().command_line(sys.argv[1:])
