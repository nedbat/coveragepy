"""Command-line support for Coverage."""

import getopt, sys

from coverage.execfile import run_python_file

USAGE = r"""
Coverage version %(__version__)s

Usage:

coverage -x [-p] [-L] MODULE.py [ARG1 ARG2 ...]
    Execute the module, passing the given command-line arguments, collecting
    coverage data.  With the -p option, include the machine name and process
    ID in the .coverage file name.  With -L, measure coverage even inside the
    Python standard library, which isn't done by default.

coverage -e
    Erase collected coverage data.

coverage -c
    Combine data from multiple coverage files (as created by -p option above)
    and store it into a single file representing the union of the coverage.

coverage -r [-m] [-i] [-o DIR,...] [FILE1 FILE2 ...]
    Report on the statement coverage for the given files.  With the -m
    option, show line numbers of the statements that weren't executed.

coverage -b -d DIR [-i] [-o DIR,...] [FILE1 FILE2 ...]
    Create an HTML report of the coverage of the given files.  Each file gets
    its own page, with the file listing decorated to show executed, excluded,
    and missed lines.

coverage -a [-d DIR] [-i] [-o DIR,...] [FILE1 FILE2 ...]
    Make annotated copies of the given files, marking statements that
    are executed with > and statements that are missed with !.

-d DIR
    Write output files for -b or -a to this directory.

-i  Ignore errors while reporting or annotating.

-o DIR,...
    Omit reporting or annotating files when their filename path starts with
    a directory listed in the omit list.
    e.g. coverage -i -r -o c:\python25,lib\enthought\traits

-h  Print this help.

Coverage data is saved in the file .coverage by default.  Set the
COVERAGE_FILE environment variable to save it somewhere else.
""".strip()


class CoverageScript:
    """The command-line interface to Coverage."""
    
    def __init__(self):
        import coverage
        self.covpkg = coverage

    def help(self, error=None):
        """Display an error message, or the usage for Coverage."""
        if error:
            print error
            print "Use -h for help."
        else:
            print USAGE % self.covpkg.__dict__

    def command_line(self, argv, help_fn=None):
        """The bulk of the command line interface to Coverage.
        
        `argv` is the argument list to process.
        `help_fn` is the help function to use when something goes wrong.
        
        """
        # Collect the command-line options.
        help_fn = help_fn or self.help
        OK, ERR = 0, 1
        settings = {}
        optmap = {
            '-a': 'annotate',
            '-b': 'html',
            '-c': 'combine',
            '-d:': 'directory=',
            '-e': 'erase',
            '-h': 'help',
            '-i': 'ignore-errors',
            '-L': 'stdlib',
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
            for j in ['annotate', 'html', 'report', 'combine']:
                if settings.get(i) and settings.get(j):
                    help_fn("You can't specify the '%s' and '%s' "
                              "options at the same time." % (i, j))
                    return ERR

        args_needed = (settings.get('execute')
                       or settings.get('annotate')
                       or settings.get('html')
                       or settings.get('report'))
        action = (settings.get('erase') 
                  or settings.get('combine')
                  or args_needed)
        if not action:
            help_fn(
                "You must specify at least one of -e, -x, -c, -r, -a, or -b."
                )
            return ERR
        if not args_needed and args:
            help_fn("Unexpected arguments: %s" % " ".join(args))
            return ERR
        
        # Do something.
        self.coverage = self.covpkg.coverage(
            parallel_mode = settings.get('parallel-mode'),
            cover_stdlib = settings.get('stdlib')
            )
        self.coverage.get_ready()

        if settings.get('erase'):
            self.coverage.erase()
        
        if settings.get('execute'):
            if not args:
                help_fn("Nothing to do.")
                return ERR
            
            # Run the script.
            self.coverage.start()
            try:
                run_python_file(args[0], args)
            finally:
                self.coverage.stop()
        
        if settings.get('combine'):
            self.coverage.combine()

        # Remaining actions are reporting, with some common options.
        show_missing = settings.get('show-missing')
        directory = settings.get('directory=')
        report_args = {
            'morfs': args,
            'ignore_errors': settings.get('ignore-errors'),
            }

        omit = settings.get('omit=')
        if omit:
            omit = omit.split(',')
        report_args['omit_prefixes'] = omit
        
        if settings.get('report'):
            self.coverage.report(show_missing=show_missing, **report_args)
        if settings.get('annotate'):
            self.coverage.annotate(directory=directory, **report_args)
        if settings.get('html'):
            self.coverage.html_report(directory=directory, **report_args)

        return OK
    

def main():
    """The main entrypoint to Coverage.
    
    This is installed as the script entrypoint.
    
    """
    return CoverageScript().command_line(sys.argv[1:])
