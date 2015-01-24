"""Command-line support for Coverage."""

import glob
import optparse
import os
import sys
import traceback

from coverage import env
from coverage.execfile import run_python_file, run_python_module
from coverage.misc import CoverageException, ExceptionDuringRun, NoSource
from coverage.debug import info_formatter, info_header


class Opts(object):
    """A namespace class for individual options we'll build parsers from."""

    append = optparse.make_option(
        '-a', '--append', action='store_false', dest="erase_first",
        help="Append coverage data to .coverage, otherwise it is started "
                "clean with each run."
        )
    branch = optparse.make_option(
        '', '--branch', action='store_true',
        help="Measure branch coverage in addition to statement coverage."
        )
    CONCURRENCY_CHOICES = ["thread", "gevent", "greenlet", "eventlet"]
    concurrency = optparse.make_option(
        '', '--concurrency', action='store', metavar="LIB",
        choices=CONCURRENCY_CHOICES,
        help="Properly measure code using a concurrency library. "
            "Valid values are: %s." % ", ".join(CONCURRENCY_CHOICES)
        )
    debug = optparse.make_option(
        '', '--debug', action='store', metavar="OPTS",
        help="Debug options, separated by commas"
        )
    directory = optparse.make_option(
        '-d', '--directory', action='store', metavar="DIR",
        help="Write the output files to DIR."
        )
    fail_under = optparse.make_option(
        '', '--fail-under', action='store', metavar="MIN", type="int",
        help="Exit with a status of 2 if the total coverage is less than MIN."
        )
    help = optparse.make_option(
        '-h', '--help', action='store_true',
        help="Get help on this command."
        )
    ignore_errors = optparse.make_option(
        '-i', '--ignore-errors', action='store_true',
        help="Ignore errors while reading source files."
        )
    include = optparse.make_option(
        '', '--include', action='store',
        metavar="PAT1,PAT2,...",
        help="Include only files whose paths match one of these patterns."
                "Accepts shell-style wildcards, which must be quoted."
        )
    pylib = optparse.make_option(
        '-L', '--pylib', action='store_true',
        help="Measure coverage even inside the Python installed library, "
                "which isn't done by default."
        )
    show_missing = optparse.make_option(
        '-m', '--show-missing', action='store_true',
        help="Show line numbers of statements in each module that weren't "
                "executed."
        )
    skip_covered = optparse.make_option(
        '--skip-covered', action='store_true',
        help="Skip files with 100% coverage."
        )
    omit = optparse.make_option(
        '', '--omit', action='store',
        metavar="PAT1,PAT2,...",
        help="Omit files whose paths match one of these patterns. "
                "Accepts shell-style wildcards, which must be quoted."
        )
    output_xml = optparse.make_option(
        '-o', '', action='store', dest="outfile",
        metavar="OUTFILE",
        help="Write the XML report to this file. Defaults to 'coverage.xml'"
        )
    parallel_mode = optparse.make_option(
        '-p', '--parallel-mode', action='store_true',
        help="Append the machine name, process id and random number to the "
                ".coverage data file name to simplify collecting data from "
                "many processes."
        )
    module = optparse.make_option(
        '-m', '--module', action='store_true',
        help="<pyfile> is an importable Python module, not a script path, "
                "to be run as 'python -m' would run it."
        )
    rcfile = optparse.make_option(
        '', '--rcfile', action='store',
        help="Specify configuration file.  Defaults to '.coveragerc'"
        )
    source = optparse.make_option(
        '', '--source', action='store', metavar="SRC1,SRC2,...",
        help="A list of packages or directories of code to be measured."
        )
    timid = optparse.make_option(
        '', '--timid', action='store_true',
        help="Use a simpler but slower trace method.  Try this if you get "
                "seemingly impossible results!"
        )
    title = optparse.make_option(
        '', '--title', action='store', metavar="TITLE",
        help="A text string to use as the title on the HTML."
        )
    version = optparse.make_option(
        '', '--version', action='store_true',
        help="Display version information and exit."
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
            action=None,
            branch=None,
            concurrency=None,
            debug=None,
            directory=None,
            fail_under=None,
            help=None,
            ignore_errors=None,
            include=None,
            omit=None,
            parallel_mode=None,
            module=None,
            pylib=None,
            rcfile=True,
            show_missing=None,
            skip_covered=None,
            source=None,
            timid=None,
            title=None,
            erase_first=None,
            version=None,
            )

        self.disable_interspersed_args()
        self.help_fn = self.help_noop

    def help_noop(self, error=None, topic=None, parser=None):
        """No-op help function."""
        pass

    class OptionParserError(Exception):
        """Used to stop the optparse error handler ending the process."""
        pass

    def parse_args_ok(self, args=None, options=None):
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


class GlobalOptionParser(CoverageOptionParser):
    """Command-line parser for coverage.py global option arguments."""

    def __init__(self):
        super(GlobalOptionParser, self).__init__()

        self.add_options([
            Opts.help,
            Opts.version,
        ])


class CmdOptionParser(CoverageOptionParser):
    """Parse one of the new-style commands for coverage.py."""

    def __init__(self, action, options=None, defaults=None, usage=None,
                description=None
                ):
        """Create an OptionParser for a coverage command.

        `action` is the slug to put into `options.action`.
        `options` is a list of Option's for the command.
        `defaults` is a dict of default value for options.
        `usage` is the usage string to display in help.
        `description` is the description of the command, for the help text.

        """
        if usage:
            usage = "%prog " + usage
        super(CmdOptionParser, self).__init__(
            prog="coverage %s" % action,
            usage=usage,
            description=description,
        )
        self.set_defaults(action=action, **(defaults or {}))
        if options:
            self.add_options(options)
        self.cmd = action

    def __eq__(self, other):
        # A convenience equality, so that I can put strings in unit test
        # results, and they will compare equal to objects.
        return (other == "<CmdOptionParser:%s>" % self.cmd)

GLOBAL_ARGS = [
    Opts.debug,
    Opts.help,
    Opts.rcfile,
    ]

CMDS = {
    'annotate': CmdOptionParser("annotate",
        [
            Opts.directory,
            Opts.ignore_errors,
            Opts.omit,
            Opts.include,
            ] + GLOBAL_ARGS,
        usage = "[options] [modules]",
        description = "Make annotated copies of the given files, marking "
            "statements that are executed with > and statements that are "
            "missed with !."
        ),

    'combine': CmdOptionParser("combine", GLOBAL_ARGS,
        usage = " ",
        description = "Combine data from multiple coverage files collected "
            "with 'run -p'.  The combined results are written to a single "
            "file representing the union of the data."
        ),

    'debug': CmdOptionParser("debug", GLOBAL_ARGS,
        usage = "<topic>",
        description = "Display information on the internals of coverage.py, "
            "for diagnosing problems. "
            "Topics are 'data' to show a summary of the collected data, "
            "or 'sys' to show installation information."
        ),

    'erase': CmdOptionParser("erase", GLOBAL_ARGS,
        usage = " ",
        description = "Erase previously collected coverage data."
        ),

    'help': CmdOptionParser("help", GLOBAL_ARGS,
        usage = "[command]",
        description = "Describe how to use coverage.py"
        ),

    'html': CmdOptionParser("html",
        [
            Opts.directory,
            Opts.fail_under,
            Opts.ignore_errors,
            Opts.omit,
            Opts.include,
            Opts.title,
            ] + GLOBAL_ARGS,
        usage = "[options] [modules]",
        description = "Create an HTML report of the coverage of the files.  "
            "Each file gets its own page, with the source decorated to show "
            "executed, excluded, and missed lines."
        ),

    'report': CmdOptionParser("report",
        [
            Opts.fail_under,
            Opts.ignore_errors,
            Opts.omit,
            Opts.include,
            Opts.show_missing,
            Opts.skip_covered
            ] + GLOBAL_ARGS,
        usage = "[options] [modules]",
        description = "Report coverage statistics on modules."
        ),

    'run': CmdOptionParser("run",
        [
            Opts.append,
            Opts.branch,
            Opts.concurrency,
            Opts.pylib,
            Opts.parallel_mode,
            Opts.module,
            Opts.timid,
            Opts.source,
            Opts.omit,
            Opts.include,
            ] + GLOBAL_ARGS,
        defaults = {'erase_first': True},
        usage = "[options] <pyfile> [program options]",
        description = "Run a Python program, measuring code execution."
        ),

    'xml': CmdOptionParser("xml",
        [
            Opts.fail_under,
            Opts.ignore_errors,
            Opts.omit,
            Opts.include,
            Opts.output_xml,
            ] + GLOBAL_ARGS,
        usage = "[options] [modules]",
        description = "Generate an XML report of coverage results."
        ),
    }


OK, ERR, FAIL_UNDER = 0, 1, 2


class CoverageScript(object):
    """The command-line interface to Coverage."""

    def __init__(self, _covpkg=None, _run_python_file=None,
                 _run_python_module=None, _help_fn=None):
        # _covpkg is for dependency injection, so we can test this code.
        if _covpkg:
            self.covpkg = _covpkg
        else:
            import coverage
            self.covpkg = coverage

        # For dependency injection:
        self.run_python_file = _run_python_file or run_python_file
        self.run_python_module = _run_python_module or run_python_module
        self.help_fn = _help_fn or self.help
        self.global_option = False

        self.coverage = None

    def command_line(self, argv):
        """The bulk of the command line interface to Coverage.

        `argv` is the argument list to process.

        Returns 0 if all is well, 1 if something went wrong.

        """
        # Collect the command-line options.
        if not argv:
            self.help_fn(topic='minimum_help')
            return OK

        # The command syntax we parse depends on the first argument.  Global
        # switch syntax always starts with an option.
        self.global_option = argv[0].startswith('-')
        if self.global_option:
            parser = GlobalOptionParser()
        else:
            parser = CMDS.get(argv[0])
            if not parser:
                self.help_fn("Unknown command: '%s'" % argv[0])
                return ERR
            argv = argv[1:]

        parser.help_fn = self.help_fn
        ok, options, args = parser.parse_args_ok(argv)
        if not ok:
            return ERR

        # Handle help and version.
        if self.do_help(options, args, parser):
            return OK

        # Check for conflicts and problems in the options.
        if not self.args_ok(options, args):
            return ERR

        # Listify the list options.
        source = unshell_list(options.source)
        omit = unshell_list(options.omit)
        include = unshell_list(options.include)
        debug = unshell_list(options.debug)

        # Do something.
        self.coverage = self.covpkg.coverage(
            data_suffix = options.parallel_mode,
            cover_pylib = options.pylib,
            timid = options.timid,
            branch = options.branch,
            config_file = options.rcfile,
            source = source,
            omit = omit,
            include = include,
            debug = debug,
            concurrency = options.concurrency,
            )

        if options.action == "debug":
            return self.do_debug(args)

        if options.action == "erase" or options.erase_first:
            self.coverage.erase()
        else:
            self.coverage.load()

        if options.action == "run":
            self.do_run(options, args)

        if options.action == "combine":
            self.coverage.combine()
            self.coverage.save()

        # Remaining actions are reporting, with some common options.
        report_args = dict(
            morfs = unglob_args(args),
            ignore_errors = options.ignore_errors,
            omit = omit,
            include = include,
            )

        total = None
        if options.action == "report":
            total = self.coverage.report(
                show_missing=options.show_missing,
                skip_covered=options.skip_covered, **report_args)
        if options.action == "annotate":
            self.coverage.annotate(
                directory=options.directory, **report_args)
        if options.action == "html":
            total = self.coverage.html_report(
                directory=options.directory, title=options.title,
                **report_args)
        if options.action == "xml":
            outfile = options.outfile
            total = self.coverage.xml_report(outfile=outfile, **report_args)

        if total is not None:
            # Apply the command line fail-under options, and then use the config
            # value, so we can get fail_under from the config file.
            if options.fail_under is not None:
                self.coverage.config["report:fail_under"] = options.fail_under

            if self.coverage.config["report:fail_under"]:

                # Total needs to be rounded, but be careful of 0 and 100.
                if 0 < total < 1:
                    total = 1
                elif 99 < total < 100:
                    total = 99
                else:
                    total = round(total)

                if total >= self.coverage.config["report:fail_under"]:
                    return OK
                else:
                    return FAIL_UNDER

        return OK

    def help(self, error=None, topic=None, parser=None):
        """Display an error message, or the named topic."""
        assert error or topic or parser
        if error:
            print(error)
            print("Use 'coverage help' for help.")
        elif parser:
            print(parser.format_help().strip())
        else:
            help_msg = HELP_TOPICS.get(topic, '').strip()
            if help_msg:
                print(help_msg % self.covpkg.__dict__)
            else:
                print("Don't know topic %r" % topic)

    def do_help(self, options, args, parser):
        """Deal with help requests.

        Return True if it handled the request, False if not.

        """
        # Handle help.
        if options.help:
            if self.global_option:
                self.help_fn(topic='help')
            else:
                self.help_fn(parser=parser)
            return True

        if options.action == "help":
            if args:
                for a in args:
                    parser = CMDS.get(a)
                    if parser:
                        self.help_fn(parser=parser)
                    else:
                        self.help_fn(topic=a)
            else:
                self.help_fn(topic='help')
            return True

        # Handle version.
        if options.version:
            self.help_fn(topic='version')
            return True

        return False

    def args_ok(self, options, args):
        """Check for conflicts and problems in the options.

        Returns True if everything is OK, or False if not.

        """
        if options.action == "run" and not args:
            self.help_fn("Nothing to do.")
            return False

        return True

    def do_run(self, options, args):
        """Implementation of 'coverage run'."""

        # Set the first path element properly.
        old_path0 = sys.path[0]

        # Run the script.
        self.coverage.start()
        code_ran = True
        try:
            if options.module:
                sys.path[0] = ''
                self.run_python_module(args[0], args)
            else:
                filename = args[0]
                sys.path[0] = os.path.abspath(os.path.dirname(filename))
                self.run_python_file(filename, args)
        except NoSource:
            code_ran = False
            raise
        finally:
            self.coverage.stop()
            if code_ran:
                self.coverage.save()

            # Restore the old path
            sys.path[0] = old_path0

    def do_debug(self, args):
        """Implementation of 'coverage debug'."""

        if not args:
            self.help_fn("What information would you like: data, sys?")
            return ERR
        for info in args:
            if info == 'sys':
                sysinfo = self.coverage.sysinfo()
                print(info_header("sys"))
                for line in info_formatter(sysinfo):
                    print(" %s" % line)
            elif info == 'data':
                self.coverage.load()
                print(info_header("data"))
                print("path: %s" % self.coverage.data.filename)
                print("has_arcs: %r" % self.coverage.data.has_arcs())
                summary = self.coverage.data.summary(fullpath=True)
                if summary:
                    plugins = self.coverage.data.plugin_data()
                    filenames = sorted(summary.keys())
                    print("\n%d files:" % len(filenames))
                    for f in filenames:
                        line = "%s: %d lines" % (f, summary[f])
                        plugin = plugins.get(f)
                        if plugin:
                            line += " [%s]" % plugin
                        print(line)
                else:
                    print("No data collected")
            else:
                self.help_fn("Don't know what you mean by %r" % info)
                return ERR
        return OK


def unshell_list(s):
    """Turn a command-line argument into a list."""
    if not s:
        return None
    if env.WINDOWS:
        # When running coverage as coverage.exe, some of the behavior
        # of the shell is emulated: wildcards are expanded into a list of
        # filenames.  So you have to single-quote patterns on the command
        # line, but (not) helpfully, the single quotes are included in the
        # argument, so we have to strip them off here.
        s = s.strip("'")
    return s.split(',')


def unglob_args(args):
    """Interpret shell wildcards for platforms that need it."""
    if env.WINDOWS:
        globbed = []
        for arg in args:
            if '?' in arg or '*' in arg:
                globbed.extend(glob.glob(arg))
            else:
                globbed.append(arg)
        args = globbed
    return args


HELP_TOPICS = {
# -------------------------
'help': """\
Coverage.py, version %(__version__)s
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
    xml         Create an XML report of coverage results.

Use "coverage help <command>" for detailed help on any command.
For more information, see %(__url__)s
""",
# -------------------------
'minimum_help': """\
Code coverage for Python.  Use 'coverage help' for help.
""",
# -------------------------
'version': """\
Coverage.py, version %(__version__)s.  %(__url__)s
""",
}


def main(argv=None):
    """The main entry point to Coverage.

    This is installed as the script entry point.

    """
    if argv is None:
        argv = sys.argv[1:]
    try:
        status = CoverageScript().command_line(argv)
    except ExceptionDuringRun as err:
        # An exception was caught while running the product code.  The
        # sys.exc_info() return tuple is packed into an ExceptionDuringRun
        # exception.
        traceback.print_exception(*err.args)
        status = ERR
    except CoverageException as err:
        # A controlled error inside coverage.py: print the message to the user.
        print(err)
        status = ERR
    except SystemExit as err:
        # The user called `sys.exit()`.  Exit with their argument, if any.
        if err.args:
            status = err.args[0]
        else:
            status = None
    return status
