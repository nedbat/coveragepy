"""Code common to test runner plugins."""

import optparse, sys
import coverage
from coverage.cmdline import pattern_list


class CoverageTestWrapper(object):
    """A coverage test wrapper.

    1) Setup the with the parsed options
    2) Call start()
    3) Run your tests
    4) Call finish()
    5) Improve your code coverage ;)

    """

    coverPackages = None

    def __init__(self, options, _covpkg=coverage):
        # _covpkg is for dependency injection, so we can test this code.

        self.options = options
        self.covpkg = _covpkg

        self.coverage = None

        self.coverTests = options.cover_tests
        self.coverPackages = options.cover_package

    def start(self):
        """Start coverage before the test suite."""
        # cover_omit is a ',' separated list if provided
        self.omit = pattern_list(self.options.cover_omit)
        self.include = pattern_list(self.options.cover_omit)

        self.coverage = self.covpkg.coverage(
            config_file = self.options.cover_rcfile,
            data_suffix = bool(self.options.cover_parallel_mode),
            cover_pylib = self.options.cover_pylib,
            timid = self.options.cover_timid,
            branch = self.options.cover_branch,
            include = self.include,
            omit = self.omit,
        )

        self.coverage.start()

    def finish(self, stream=None):
        """Finish coverage after the test suite."""
        self.coverage.stop()
        self.coverage.save()

        modules = [module for name, module in sys.modules.items()
                   if self._want_module(name, module)]

        # Remaining actions are reporting, with some common options.
        report_args = dict(
            morfs = modules,
            ignore_errors = True,
            omit = self.omit,
            include = self.include,
            )

        do_report = ('report' in self.options.cover_reports or
                        not self.options.cover_reports)

        if do_report:
            self.coverage.report(
                    show_missing=self.options.cover_show_missing,
                    file=stream, **report_args)
        if 'annotate' in self.options.cover_reports:
            self.coverage.annotate(
                    directory=self.options.cover_directory, **report_args)
        if 'html' in self.options.cover_reports:
            self.coverage.html_report(
                    directory=self.options.cover_directory, **report_args)
        if 'xml' in self.options.cover_reports:
            outfile = self.options.cover_outfile
            if outfile == '-':
                outfile = None
            self.coverage.xml_report(outfile=outfile, **report_args)

        return

    def _want_module(self, name, module):
        """Determine if this module should be reported on."""
        for package in self.coverPackages:
            if module is not None and name.startswith(package):
                return True

        return False


# The command-line options for the plugin.
OPTIONS = [
    optparse.Option('--cover-rcfile', action='store', metavar="RCFILE",
                    help="Specify configuration file.  ['.coveragerc']",
                    default=True),

    optparse.Option('--cover-report', action='append', default=[],
                    dest='cover_reports', type="choice",
                    choices=['annotate', 'html', 'report', 'xml'],
                    help=("Choose what coverage report(s) to create: "
                        "annotate: Annotated source files; "
                        "html: Browsable HTML report; "
                        "report: Simple text report; "
                        "xml: Cobertura-compatible XML report.")
                    ),

    optparse.Option('--cover-package', action='append', default=[],
                    dest="cover_package", metavar="COVER_PACKAGE",
                    help=("Restrict coverage output to selected package "
                          "- can be specified multiple times")),

    optparse.Option("--cover-tests", action="store_true", dest="cover_tests",
                    metavar="[NOSE_COVER_TESTS]", default=False,
                    help="Include test modules in coverage report "),

    optparse.Option('--cover-branch', action='store_true',
                    help="Measure branch execution."),

    optparse.Option('--cover-directory', action='store', metavar="DIR",
                    help="Write the output files to DIR."),

    optparse.Option('--cover-pylib', action='store_true',
                    help=("Measure coverage even inside the Python installed "
                         "library, which isn't done by default.")),

    optparse.Option('--cover-show-missing', action='store_true',
                    help=("Show line numbers of statements in each module "
                         "that weren't executed.")),

    optparse.Option('--cover-include', action='store',
                    metavar="PAT1,PAT2,...", default='',
                    help=("Include files when their filename path matches one "
                         "of these file patterns.")),

    optparse.Option('--cover-omit', action='store',
                    metavar="PAT1,PAT2,...", default='',
                    help=("Omit files when their filename path matches one "
                         "of these file patterns.")),

    optparse.Option('--cover-outfile', action='store', metavar="OUTFILE",
                    help=("Write the XML report to this file. Defaults to "
                         "'coverage.xml'")),

    optparse.Option('--cover-parallel-mode', action='store_true',
                    help=("Include the machine name and process id in the "
                          ".coverage data file name.")),

    optparse.Option('--cover-timid', action='store_true',
                    help=("Use a simpler but slower trace method.  Try this "
                          "if you get seemingly impossible results!")),

    optparse.Option('--cover-append', action='store_false',
                    help=("Append coverage data to .coverage, otherwise it "
                          "is started clean with each run."))
    ]
