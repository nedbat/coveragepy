import optparse

class CoverageTestWrapper(object):
    """
    A Coverage Test Wrapper.
    
    1) Setup the with the parsed options
    2) Call start()
    3) Run your tests
    4) Call finish()
    5) Imporve your code coverage ;)
    """
    
    def __init__(self, options, _covpkg=None):
        self.options = options
        
        # _covpkg is for dependency injection, so we can test this code.
        if _covpkg:
            self.covpkg = _covpkg
        else:
            import coverage
            self.covpkg = coverage
        
        self.coverage = None
    
    def start(self):
        # Set up coverage
        self.coverage = self.covpkg.coverage(
            data_suffix = bool(self.options.cover_parallel_mode),
            cover_pylib = self.options.cover_pylib,
            timid = self.options.cover_timid,
            branch = self.options.cover_branch,
        )
        
        # Run the script.
        self.coverage.start()
        
    def finish(self):
        # end coverage and save the results
        self.coverage.stop()
        self.coverage.save()
        
        # Remaining actions are reporting, with some common self.options.
        report_args = {
            'morfs': [],
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
                show_missing=self.options.cover_show_missing, **report_args)
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

class Options(object):
    """A namespace class for individual options we'll build parsers from."""
    
    action = optparse.Option('',
                '--cover-action', action='append', default=None,
                dest='cover_actions', type="choice", choices=['annotate', 'html', 'report', 'xml'],
                help="""
                    annotate    Annotate source files with execution information.
                    html        Create an HTML report.
                    report      Report coverage stats on modules.
                    xml         Create an XML report of coverage results.
                """.strip())
    
    branch = optparse.Option(
        '--cover-branch', action='store_true',
        help="Measure branch execution. HIGHLY EXPERIMENTAL!"
        )
    directory = optparse.Option(
        '--cover-directory', action='store',
        metavar="DIR",
        help="Write the output files to DIR."
        )
    ignore_errors = optparse.Option(
        '--cover-ignore-errors', action='store_true',
        help="Ignore errors while reading source files."
        )
    pylib = optparse.Option(
        '--cover-pylib', action='store_true',
        help="Measure coverage even inside the Python installed library, "
                "which isn't done by default."
        )
    show_missing = optparse.Option(
        '--cover-show-missing', action='store_true',
        help="Show line numbers of statements in each module that weren't "
                "executed."
        )
    omit = optparse.Option(
        '--cover-omit', action='store',
        metavar="PRE1,PRE2,...",
        default='',
        help="Omit files when their filename path starts with one of these "
                "prefixes."
        )
    output_xml = optparse.Option(
        '--cover-outfile', action='store',
        metavar="OUTFILE",
        help="Write the XML report to this file. Defaults to 'coverage.xml'"
        )
    parallel_mode = optparse.Option(
        '--cover-parallel-mode', action='store_true',
        help="Include the machine name and process id in the .coverage "
                "data file name."
        )
    timid = optparse.Option(
        '--cover-timid', action='store_true',
        help="Use a simpler but slower trace method.  Try this if you get "
                "seemingly impossible results!"
        )
    append = optparse.Option(
        '--cover-append', action='store_false',
        help="Append coverage data to .coverage, otherwise it is started "
                "clean with each run."
        )
