"""Reporter foundation for Coverage."""

import os
from coverage.codeunit import code_unit_factory
from coverage.misc import CoverageException, NoSource

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

        # The directory into which to place the report, used by some derived
        # classes.
        self.directory = None

    def find_code_units(self, morfs, omit, include):
        """Find the code units we'll report on.

        `morfs` is a list of modules or filenames.

        See `coverage.report()` for other arguments.

        """
        morfs = morfs or self.coverage.data.executed_files()
        self.code_units = code_unit_factory(
                            morfs, self.coverage.file_locator, omit, include
                            )
        self.code_units.sort()

    def report_files(self, report_fn, morfs, directory=None,
                        omit=None, include=None):
        """Run a reporting function on a number of morfs.

        `report_fn` is called for each relative morf in `morfs`.

        `include` is a list of filename patterns. CodeUnits that match
        those patterns will be included in the list. CodeUnits that match
        `omit` will be omitted from the list.

        """
        self.find_code_units(morfs, omit, include)

        if not self.code_units:
            raise CoverageException("No data to report.")

        self.directory = directory
        if self.directory and not os.path.exists(self.directory):
            os.makedirs(self.directory)

        for cu in self.code_units:
            try:
                report_fn(cu, self.coverage._analyze(cu))
            except NoSource:
                if not self.ignore_errors:
                    raise
