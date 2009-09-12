"""Command-line support for Coverage."""

import optparse, sys

from coverage.execfile import run_python_file


class opts:
    directory = optparse.Option(
        '-d', '--directory', action='store', dest='directory',
        )
    help = optparse.Option(
        '-h', '--help', action='store_true', dest='help',
        )
    ignore_errors = optparse.Option(
        '-i', '--ignore-errors', action='store_true',
        )
    pylib = optparse.Option(
        '-L', '--pylib', action='store_true',
        help="Measure coverage even inside the Python installed library, which isn't done by default."
        )
    show_missing = optparse.Option(
        '-m', '--show-missing', action='store_true',
        )
    omit = optparse.Option(
        '-o', '--omit', action='store',
        )
    parallel_mode = optparse.Option(
        '-p', '--parallel-mode', action='store_true',
        help="Include the machine name and process id in the .coverage data file name."
        )
    timid = optparse.Option(
        '', '--timid', action='store_true',
        help="Use a simpler but slower trace method.  Use this if you get seemingly impossible results!"
        )

    
class CoverageOptionParser(optparse.OptionParser, object):
    """Base OptionParser for coverage.
    
    Problems don't exit the program.
    Defaults are initialized for all options.
    
    """

    def __init__(self, *args, **kwargs):
        super(CoverageOptionParser, self).__init__(
            add_help_option=False, *args, **kwargs
            )
        self.set_defaults(
            actions=[],
            directory=None,
            help=None,
            ignore_errors=None,
            omit=None,
            parallel_mode=None,
            pylib=None,
            show_missing=None,
            timid=None,
            )

        self.disable_interspersed_args()
        self.help_fn = None

    class OptionParserError(Exception):
        """Used to stop the optparse error handler ending the process."""
        pass
    
    def parse_args(self, args=None, options=None):
        """Call optparse.parse_args, but return a triple:
        
        (ok, options, args)
        
        """
        try:
            options, args = super(CoverageOptionParser, self).parse_args(args, options)
        except self.OptionParserError:
            return False, None, None
        return True, options, args
        
    def error(self, msg):
        """Override optparse.error so sys.exit doesn't get called."""
        self.help_fn(msg)
        raise self.OptionParserError


class ClassicOptionParser(CoverageOptionParser):
    """Command-line parser for coverage.py classic arguments."""

    def __init__(self):
        super(ClassicOptionParser, self).__init__()
        
        self.add_action('-a', '--annotate', 'annotate')
        self.add_action('-b', '--html', 'html')
        self.add_action('-c', '--combine', 'combine')
        self.add_action('-e', '--erase', 'erase')
        self.add_action('-r', '--report', 'report')
        self.add_action('-x', '--execute', 'execute')

        self.add_options([
            opts.directory,
            opts.help,
            opts.ignore_errors,
            opts.pylib,
            opts.show_missing,
            opts.omit,
            opts.parallel_mode,
            opts.timid,
        ])

    def add_action(self, dash, dashdash, action_code):
        """Add a specialized option that is the action to execute."""
        option = self.add_option(dash, dashdash, action='callback',
            callback=self._append_action
            )
        option.action_code = action_code
        
    def _append_action(self, option, opt_unused, value_unused, parser):
        """Callback for an option that adds to the `actions` list."""
        parser.values.actions.append(option.action_code)


class NewOptionParser(CoverageOptionParser):
    """Parse one of the new-style commands for coverage.py."""
    
    def __init__(self, action):
        super(NewOptionParser, self).__init__(
            usage="coverage %s [blah]" % action
        )
        self.set_defaults(actions=[action])


class RunOptionParser(NewOptionParser):
    def __init__(self):
        super(RunOptionParser, self).__init__("execute")
        self.add_options([
            opts.pylib,
            opts.parallel_mode,
            opts.timid,
        ])


CMDS = {
    'run': RunOptionParser(),
}


class CoverageScript:
    """The command-line interface to Coverage."""
    
    def __init__(self, _covpkg=None, _run_python_file=None, _help_fn=None):
        # _covpkg is for dependency injection, so we can test this code.
        if _covpkg:
            self.covpkg = _covpkg
        else:
            import coverage
            self.covpkg = coverage
        
        # _run_python_file is for dependency injection also.
        self.run_python_file = _run_python_file or run_python_file
        
        # _help_fn is for dependency injection.
        self.help_fn = _help_fn or self.help
        
        self.coverage = None

    def help(self, error=None, topic=None):
        """Display an error message, or the named topic."""
        assert error or topic
        if error:
            print error
            print "Use -h for help."
        else:
            print HELP_TOPICS[topic].strip() % self.covpkg.__dict__

    def command_line(self, argv):
        """The bulk of the command line interface to Coverage.
        
        `argv` is the argument list to process.

        Returns 0 if all is well, 1 if something went wrong.

        """
        # Collect the command-line options.
        OK, ERR = 0, 1
        
        if not argv:
            self.help_fn(
                "Code coverage for Python.  Use -h for help."
                )
            return OK

        # The command syntax we parse depends on the first argument.  Classic
        # syntax always starts with an option.
        if argv[0].startswith('-'):
            parser = ClassicOptionParser()
        else:
            parser = CMDS.get(argv[0])
            if not parser:
                self.help_fn("Unknown command: '%s'" % argv[0])
                return ERR
            argv = argv[1:]

        parser.help_fn = self.help_fn
        ok, options, args = parser.parse_args(argv)
        if not ok:
            return ERR

        if options.help:
            self.help_fn(topic='usage')
            return OK

        # Check for conflicts and problems in the options.
        for i in ['erase', 'execute']:
            for j in ['annotate', 'html', 'report', 'combine']:
                if (i in options.actions) and (j in options.actions):
                    self.help_fn("You can't specify the '%s' and '%s' "
                              "options at the same time." % (i, j))
                    return ERR

        if not options.actions:
            self.help_fn(
                "You must specify at least one of -e, -x, -c, -r, -a, or -b."
                )
            return ERR
        args_needed = (
            'execute' in options.actions or
            'annotate' in options.actions or
            'html' in options.actions or
            'report' in options.actions
            )
        if not args_needed and args:
            self.help_fn("Unexpected arguments: %s" % " ".join(args))
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
                self.help_fn("Nothing to do.")
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


HELP_TOPICS = {

'usage': r"""
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
""",

}


def main():
    """The main entrypoint to Coverage.
    
    This is installed as the script entrypoint.
    
    """
    return CoverageScript().command_line(sys.argv[1:])
