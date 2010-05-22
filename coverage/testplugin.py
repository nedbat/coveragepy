import os
import re
import sys
import optparse
from types import ListType

import coverage

class CoverageTestWrapper(object):
    """
    A Coverage Test Wrapper.
    
    1) Setup the with the parsed options
    2) Call start()
    3) Run your tests
    4) Call finish()
    5) Improve your code coverage ;)
    """
    
    coverTests = False
    coverPackages = None

    def __init__(self, options, _covpkg=None):
        self.options = options
        
        # _covpkg is for dependency injection, so we can test this code.
        if _covpkg:
            self.covpkg = _covpkg
        else:
            import coverage
            self.covpkg = coverage
        
        self.coverage = None

        self.coverTests = options.cover_tests
        self.coverPackage = options.cover_package
    
    def start(self):
        # Set up coverage
        self.coverage = self.covpkg.coverage(
            data_suffix = bool(self.options.cover_parallel_mode),
            cover_pylib = self.options.cover_pylib,
            timid = self.options.cover_timid,
            branch = self.options.cover_branch,
        )

        self.skipModules = sys.modules.keys()[:]
        
        # Run the script.
        self.coverage.start()
        
    def finish(self, stream=None):
        # end coverage and save the results
        self.coverage.stop()
        self.coverage.save()

        modules = []
        if self.coverPackage:
            for name, module in sys.modules.items():
                if module is not None and name.startswith(self.coverPackage):
                    modules.append(module)

        # Remaining actions are reporting, with some common self.options.
        report_args = {
            'morfs': modules,
            'ignore_errors': self.options.cover_ignore_errors,
            }
            
        # Handle any omits
        # Allow pointing to a file as well
        try:
            omit_file = open(self.options.cover_omit)
            omit_prefixes = [line.strip() for line in omit_file.readlines()]
            report_args['omit_prefixes'] = omit_prefixes
        except:
            omit = self.options.cover_omit.split(',')
            report_args['omit_prefixes'] = omit

        if 'report' in self.options.cover_actions:
            self.coverage.report(
                show_missing=self.options.cover_show_missing,
                file=stream, **report_args)
        if 'annotate' in self.options.cover_actions:
            self.coverage.annotate(
                directory=self.options.cover_directory, **report_args)
        if 'html' in self.options.cover_actions:
            self.coverage.html_report(
                directory=self.options.cover_directory, **report_args)
        if 'xml' in self.options.cover_actions:
            outfile = self.options.cover_outfile
            if outfile == '-':
                outfile = None
            self.coverage.xml_report(outfile=outfile, **report_args)
        
        return

options = [
    optparse.Option('',
                '--cover-action', action='append', default=['report'],
                dest='cover_actions', type="choice", choices=['annotate', 'html', 'report', 'xml'],
                help="""\
annotate    Annotate source files with execution information.
html        Create an HTML report.
report      Report coverage stats on modules.
xml         Create an XML report of coverage results.
""".strip()),
    optparse.Option(
        '--cover-package', action='store',
        dest="cover_package",
        metavar="COVER_PACKAGE",
        help="Restrict coverage output to selected package"
        ),
    optparse.Option("--cover-tests", action="store_true",
        dest="cover_tests",
        metavar="[NOSE_COVER_TESTS]",
        default=False,
        help="Include test modules in coverage report "),
    optparse.Option(
        '--cover-branch', action='store_true',
        help="Measure branch execution. HIGHLY EXPERIMENTAL!"
        ),
    optparse.Option(
        '--cover-directory', action='store',
        metavar="DIR",
        help="Write the output files to DIR."
        ),
    optparse.Option(
        '--cover-ignore-errors', action='store_true',
        help="Ignore errors while reading source files."
        ),
    optparse.Option(
        '--cover-pylib', action='store_true',
        help="Measure coverage even inside the Python installed library, "
                "which isn't done by default."
        ),
    optparse.Option(
        '--cover-show-missing', action='store_true',
        help="Show line numbers of statements in each module that weren't "
                "executed."
        ),
    optparse.Option(
        '--cover-omit', action='store',
        metavar="PRE1,PRE2,...",
        default='',
        help="Omit files when their filename path starts with one of these "
                "prefixes."
        ),
    optparse.Option(
        '--cover-outfile', action='store',
        metavar="OUTFILE",
        help="Write the XML report to this file. Defaults to 'coverage.xml'"
        ),
    optparse.Option(
        '--cover-parallel-mode', action='store_true',
        help="Include the machine name and process id in the .coverage "
                "data file name."
        ),
    optparse.Option(
        '--cover-timid', action='store_true',
        help="Use a simpler but slower trace method.  Try this if you get "
                "seemingly impossible results!"
        ),
    optparse.Option(
        '--cover-append', action='store_false',
        help="Append coverage data to .coverage, otherwise it is started "
                "clean with each run."
        )
]

# py.test plugin hooks

def pytest_addoption(parser):
    """
    Get all the options from the coverage.runner and import them
    """
    group = parser.getgroup('Coverage options')
    for opt in options:
        group._addoption_instance(opt)

def pytest_configure(config):
    # Load the runner and start it up
    if config.getvalue("cover_actions"):
        config.pluginmanager.register(DoCover(config), "do_coverage")

class DoCover:
    def __init__(self, config):
        self.config = config

    def pytest_sessionstart(self):
        self.coverage = CoverageTestWrapper(self.config.option)
        # XXX maybe better to start/suspend/resume coverage
        # for each single test item
        self.coverage.start()

    def pytest_terminal_summary(self, terminalreporter):
        # Finished the tests start processing the coverage
        config = terminalreporter.config
        tw = terminalreporter._tw
        tw.sep('-', 'coverage')
        tw.line('Processing Coverage...')
        self.coverage.finish()
       

# XXX please make the following unnessary
# Monkey patch omit_filter to use regex patterns for file omits
def omit_filter(omit_prefixes, code_units):
    import re
    exclude_patterns = [re.compile(line.strip()) for line in omit_prefixes if line and not line.startswith('#')]
    filtered = []
    for cu in code_units:
        skip = False
        for pattern in exclude_patterns:
            if pattern.search(cu.filename):
                skip = True
                break
            
        if not skip:
            filtered.append(cu)
    return filtered

coverage.codeunit.omit_filter = omit_filter
