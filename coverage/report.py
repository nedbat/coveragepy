"""Reporter foundation for coverage.py"""

from coverage.codeunit import code_unit_factory

class Reporter(object):
    """A base class for all reporters."""
    
    def __init__(self, coverage, ignore_errors=False):
        """Create a reporter.
        
        `coverage` is the coverage instance. `ignore_errors` controls how
        skittish the reporter will be during file processing.

        """
        self.coverage = coverage
        self.ignore_errors = ignore_errors
        
        # The code units to report on.  Set by find_code_units.
        self.code_units = []
        
    def find_code_units(self, morfs, omit_prefixes):
        """Find the code units we'll report on.
        
        `morfs` is a list of modules or filenames. `omit_prefixes` is a list
        of prefixes to leave out of the list.
        
        """
        morfs = morfs or self.coverage.data.executed_files()
        self.code_units = code_unit_factory(morfs, self.coverage.file_locator, omit_prefixes)
        self.code_units.sort()
