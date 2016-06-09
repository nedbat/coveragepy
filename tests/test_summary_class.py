# coding: utf8
# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

"""Test text-based summary reporter for coverage.py"""

import os.path

from coverage.backward import StringIO
from coverage.backunittest import TestCase
from coverage.config import CoverageConfig
from coverage.control import Coverage
from coverage.data import CoverageData
from coverage.summary import SummaryReporter

LINES_1 = {
    __file__: {-1: 1, 7: 1},
    os.path.join(os.path.dirname(__file__), 'helpers.py'): {-1: 1, 7: 1},
}


class TestSummaryReporterConfiguration(TestCase):
    """Tests of SummaryReporter."""

    def get_coverage_data(self, lines):
        """Get a CoverageData object that includes the requested lines."""
        data = CoverageData()
        data.add_lines(lines)
        return data

    def get_summary_text(self, coverage_data, options):
        """Get text output from the SummaryReporter."""
        cov = Coverage()
        cov.data = coverage_data
        printer = SummaryReporter(cov, options)
        destination = StringIO()
        printer.report([], destination)
        return destination.getvalue()

    def test_defaults(self):
        """Run the report with no configuration options."""
        data = self.get_coverage_data(LINES_1)
        opts = CoverageConfig()
        report = self.get_summary_text(data, opts)
        self.assertNotIn('Missing', report)
        self.assertNotIn('Branch', report)

    def test_print_missing(self):
        """Run the report printing the missing lines."""
        data = self.get_coverage_data(LINES_1)
        opts = CoverageConfig()
        opts.from_args(show_missing=True)
        report = self.get_summary_text(data, opts)
        self.assertTrue('Missing' in report)
        self.assertNotIn('Branch', report)

    def test_sort_report(self):
        """Sort the text report."""
        data = self.get_coverage_data(LINES_1)
        opts = CoverageConfig()
        opts.from_args(sort='Stmts')
        report = self.get_summary_text(data, opts)
        # just the basename, to avoid pyc and directory name complexities
        filename = os.path.splitext(os.path.basename(__file__))[0]
        location1 = report.find('helpers')
        location2 = report.find(filename)
        self.assertTrue(location1 < location2)
