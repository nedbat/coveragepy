"""Command-line support for Coverage."""

import optparse, sys

from coverage.execfile import run_python_file

USAGE = r"""
Coverage version %(__version__)s
Measure, collect, and report on code coverage in Python programs.

Usage:

coverage -x [-p] [-L] [--timid] MODULE.py [ARG1 ARG2 ...]
    Execute the module, passing the given command-line arguments, collecting
    coverage data.  With the -p option, include the machine name and process
    id in the .coverage file name.  With -L, measure coverage even inside the
    Python installed library, which isn't done by default.  With --timid, use a
    simpler but slower trace method.

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


class OptionParser(optparse.OptionParser, object):
    """Command-line parser for coverage.py."""

    def __init__(self, help_fn, *args, **kwargs):
        super(OptionParser, self).__init__(
            add_help_option=False, *args, **kwargs
            )
        
        self.set_defaults(actions=[])
        self.disable_interspersed_args()

        self.help_fn = help_fn
        
        self.add_action('-a', '--annotate', 'annotate')
        self.add_action('-b', '--html', 'html')
        self.add_action('-c', '--combine', 'combine')
        self.add_option('-d', '--directory', action='store', dest='directory')
        self.add_action('-e', '--erase', 'erase')
        self.add_option('-h', '--help', action='store_true', dest='help')
        self.add_option('-i', '--ignore-errors', action='store_true')
        self.add_option('-L', '--pylib', action='store_true')
        self.add_option('-m', '--show-missing', action='store_true')
        self.add_option('-p', '--parallel-mode', action='store_true')
        self.add_action('-r', '--report', 'report')
        self.add_action('-x', '--execute', 'execute')
        self.add_option('-o', '--omit', action='store')
        self.add_option('', '--timid', action='store_true')

    def add_action(self, dash, dashdash, action):
        """Add a specialized option that is the action to execute."""
        option = self.add_option(dash, dashdash, action='callback',
            callback=self.append_action
            )
        option.action_code = action
        
    def append_action(self, option, opt_unused, value_unused, parser):
        """Callback for an option that adds to the `actions` list."""
        parser.values.actions.append(option.action_code)

    class OptionParserError(Exception):
        """Used to stop the optparse error handler ending the process."""
        pass
    
    def parse_args(self, args=None, options=None):
        """Call optparse.parse_args, but return a triple:
        
        (ok, options, args)
        
        """
        try:
            options, args = super(OptionParser, self).parse_args(args, options)
        except self.OptionParserError:
            return False, None, None
        return True, options, args
        
    def error(self, msg):
        """Override optparse.error so sys.exit doesn't get called."""
        self.help_fn(msg)
        raise self.OptionParserError


class CoverageScript:
    """The command-line interface to Coverage."""
    
    def __init__(self, _covpkg=None, _run_python_file=None):
        # _covpkg is for dependency injection, so we can test this code.
        if _covpkg:
            self.covpkg = _covpkg
        else:
            import coverage
            self.covpkg = coverage
        
        # _run_python_file is for dependency injection also.
        self.run_python_file = _run_python_file or run_python_file
        
        self.coverage = None

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
        
        parser = OptionParser(help_fn)
        ok, options, args = parser.parse_args(argv)
        if not ok:
            return ERR

        if options.help:
            help_fn()
            return OK

        # Check for conflicts and problems in the options.
        for i in ['erase', 'execute']:
            for j in ['annotate', 'html', 'report', 'combine']:
                if (i in options.actions) and (j in options.actions):
                    help_fn("You can't specify the '%s' and '%s' "
                              "options at the same time." % (i, j))
                    return ERR

        args_needed = (
            'execute' in options.actions or
            'annotate' in options.actions or
            'html' in options.actions or
            'report' in options.actions
            )
        if not options.actions:
            help_fn(
                "You must specify at least one of -e, -x, -c, -r, -a, or -b."
                )
            return ERR
        if not args_needed and args:
            help_fn("Unexpected arguments: %s" % " ".join(args))
            return ERR
        
        # Do something.
        self.coverage = self.covpkg.coverage(
            data_suffix = bool(options.parallel_mode),
            cover_pylib = options.pylib,
            timid = options.timid,
            )

        if 'erase' in options.actions:
            self.coverage.erase()
        else:
            self.coverage.load()

        if 'execute' in options.actions:
            if not args:
                help_fn("Nothing to do.")
                return ERR
            
            # Run the script.
            self.coverage.start()
            try:
                self.run_python_file(args[0], args)
            finally:
                self.coverage.stop()
                self.coverage.save()

        if 'combine' in options.actions:
            self.coverage.combine()
            self.coverage.save()

        # Remaining actions are reporting, with some common options.
        report_args = {
            'morfs': args,
            'ignore_errors': options.ignore_errors,
            }

        omit = None
        if options.omit:
            omit = options.omit.split(',')
        report_args['omit_prefixes'] = omit
        
        if 'report' in options.actions:
            self.coverage.report(
                show_missing=options.show_missing, **report_args)
        if 'annotate' in options.actions:
            self.coverage.annotate(
                directory=options.directory, **report_args)
        if 'html' in options.actions:
            self.coverage.html_report(
                directory=options.directory, **report_args)

        return OK
    

def main():
    """The main entrypoint to Coverage.
    
    This is installed as the script entrypoint.
    
    """
    return CoverageScript().command_line(sys.argv[1:])
