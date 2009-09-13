"""Command-line support for Coverage."""

import optparse, sys

from coverage.execfile import run_python_file


class Opts:
    """A namespace class for individual options we'll build parsers from."""
    
    directory = optparse.Option(
        '-d', '--directory', action='store',
        metavar="DIR",
        help="Write the output files to DIR."
        )
    help = optparse.Option(
        '-h', '--help', action='store_true',
        help="Get help on this command."
        )
    ignore_errors = optparse.Option(
        '-i', '--ignore-errors', action='store_true',
        help="Ignore errors while reading source files."
        )
    pylib = optparse.Option(
        '-L', '--pylib', action='store_true',
        help="Measure coverage even inside the Python installed library, "
                "which isn't done by default."
        )
    show_missing = optparse.Option(
        '-m', '--show-missing', action='store_true',
        help="Show line numbers of statements in each module that weren't "
                "executed."
        )
    omit = optparse.Option(
        '-o', '--omit', action='store',
        metavar="PRE1,PRE2,...",
        help="Omit files when their filename path starts with one of these "
                "prefixes."
        )
    parallel_mode = optparse.Option(
        '-p', '--parallel-mode', action='store_true',
        help="Include the machine name and process id in the .coverage "
                "data file name."
        )
    timid = optparse.Option(
        '', '--timid', action='store_true',
        help="Use a simpler but slower trace method.  Try this if you get "
                "seemingly impossible results!"
        )
    append = optparse.Option(
        '-a', '--append', action='store_false', dest="erase_first",
        help="Append coverage data to .coverage, otherwise it is started "
                "clean with each run."
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
            erase_first=None,
            )

        self.disable_interspersed_args()
        self.help_fn = lambda: None

    class OptionParserError(Exception):
        """Used to stop the optparse error handler ending the process."""
        pass
    
    def parse_args(self, args=None, options=None):
        """Call optparse.parse_args, but return a triple:
        
        (ok, options, args)
        
        """
        try:
            options, args = \
                super(CoverageOptionParser, self).parse_args(args, options)
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
            Opts.directory,
            Opts.help,
            Opts.ignore_errors,
            Opts.pylib,
            Opts.show_missing,
            Opts.omit,
            Opts.parallel_mode,
            Opts.timid,
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


class CmdOptionParser(CoverageOptionParser):
    """Parse one of the new-style commands for coverage.py."""
    
    def __init__(self, action, options=None, defaults=None, usage=None,
                cmd=None, description=None
                ):
        """Create an OptionParser for a coverage command.
        
        `action` is the slug to put into `options.actions`.
        `options` is a list of Option's for the command.
        `defaults` is a dict of default value for options.
        `usage` is the usage string to display in help.
        `cmd` is the command name, if different than `action`.
        `description` is the description of the command, for the help text.
        
        """
        if usage:
            usage = "%prog " + usage
        super(CmdOptionParser, self).__init__(
            prog="coverage %s" % (cmd or action),
            usage=usage,
            description=description,
        )
        self.set_defaults(actions=[action], **(defaults or {}))
        if options:
            self.add_options(options)
        self.cmd = cmd or action

    def __eq__(self, other):
        # A convenience equality, so that I can put strings in unit test
        # results, and they will compare equal to objects.
        return (other == "<CmdOptionParser:%s>" % self.cmd)


CMDS = {
    'annotate': CmdOptionParser("annotate",
        [
            Opts.directory,
            Opts.ignore_errors,
            Opts.omit,
            Opts.help,
            ],
        usage = "[options] [modules]",
        description = "Make annotated copies of the given files, marking "
            "statements that are executed with > and statements that are "
            "missed with !."
        ),

    'help': CmdOptionParser("help",
        usage = "[command]",
        description = "Describe how to use coverage.py"
        ),

    'html': CmdOptionParser("html",
        [
            Opts.directory,
            Opts.ignore_errors,
            Opts.omit,
            Opts.help,
            ],
        usage = "[options] [modules]",
        description = "Create an HTML report of the coverage of the files.  "
            "Each file gets its own page, with the source decorated to show "
            "executed, excluded, and missed lines."
        ),
    
    'combine': CmdOptionParser("combine",
        usage = " ",
        description = "Combine data from multiple coverage files collected "
            "with 'run -p'.  The combined results are stored into a single "
            "file representing the union of the coverage."
        ),

    'erase': CmdOptionParser("erase",
        usage = " ",
        description = "Erase previously collected coverage data."
        ),

    'report': CmdOptionParser("report",
        [
            Opts.ignore_errors,
            Opts.omit,
            Opts.show_missing,
            Opts.help,
            ],
        usage = "[options] [modules]",
        description = "Report coverage stats on modules."
        ),

    'run': CmdOptionParser("execute",
        [
            Opts.append,
            Opts.pylib,
            Opts.parallel_mode,
            Opts.timid,
            Opts.help,
            ],
        defaults = {'erase_first':True},
        cmd = "run",
        usage = "[options] <pyfile> [program options]",
        description = "Run a python program, measuring code execution."
        ),
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

    def help(self, error=None, topic=None, parser=None):
        """Display an error message, or the named topic."""
        assert error or topic or parser
        if error:
            print error
            print "Use 'coverage help' for help."
        elif parser:
            print parser.format_help(),
        else:
            # Parse out the topic we want from HELP_TOPICS
            import re
            topic_list = re.split("(?m)^=+ (\w+) =+$", HELP_TOPICS)
            topics = dict(zip(topic_list[1::2], topic_list[2::2]))
            help_msg = topics[topic].strip()
            print help_msg % self.covpkg.__dict__

    def command_line(self, argv):
        """The bulk of the command line interface to Coverage.
        
        `argv` is the argument list to process.

        Returns 0 if all is well, 1 if something went wrong.

        """
        # Collect the command-line options.
        OK, ERR = 0, 1
        
        if not argv:
            self.help_fn(topic='minimum_help')
            return OK

        # The command syntax we parse depends on the first argument.  Classic
        # syntax always starts with an option.
        classic = argv[0].startswith('-')
        if classic:
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

        # Handle help.
        if options.help:
            if classic:
                self.help_fn(topic='classic_usage')
            else:
                self.help_fn(parser=parser)
            return OK

        if "help" in options.actions:
            if args:
                for a in args:
                    parser = CMDS.get(a)
                    if parser:
                        self.help_fn(parser=parser)
            else:
                self.help_fn(topic='help')
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
        
        if 'execute' in options.actions and not args:
            self.help_fn("Nothing to do.")
            return ERR
            
        # Do something.
        self.coverage = self.covpkg.coverage(
            data_suffix = bool(options.parallel_mode),
            cover_pylib = options.pylib,
            timid = options.timid,
            )

        if 'erase' in options.actions or options.erase_first:
            self.coverage.erase()
        else:
            self.coverage.load()

        if 'execute' in options.actions:
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


HELP_TOPICS = r"""

== classic_usage ==============================================================
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

== help =======================================================================
Coverage version %(__version__)s
Measure, collect, and report on code coverage in Python programs.

usage: coverage <command> [options] [args]

Commands:
    annotate    Annotate source files with execution information.
    combine     Combine a number of data files. 
    erase       Erase previously collected coverage data.
    help        Get help on using coverage.py.
    html        Create an HTML report.
    report      Report coverage stats on modules.
    run         Run a Python program and measure code execution.

Use "coverage help <command>" for detailed help on each command.
For more information, see http://nedbatchelder.com/code/coverage

== minimum_help ===============================================================
Code coverage for Python.  Use 'coverage help' for help.

"""


def main():
    """The main entrypoint to Coverage.
    
    This is installed as the script entrypoint.
    
    """
    return CoverageScript().command_line(sys.argv[1:])
