# coding: utf8
# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

"""Test text-based summary reporter for coverage.py"""

import collections
import unittest
import os.path
import sys
if sys.version_info < (3, ):
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO
else:
    from io import StringIO
from coverage import summary, data, control, config

LINES_1 = {
    __file__: {-1: 1, 7: 1},
    os.path.join(os.path.dirname(__file__), 'helpers.py'): {-1: 1, 7: 1},
}


class TestSummaryReporterConfiguration(unittest.TestCase):
    def get_coverage_data(self, lines=LINES_1):
        """Get a CoverageData object that includes the requested lines."""
        data1 = data.CoverageData()
        data1.add_lines(lines)
        return data1

    def get_summary_text(self, coverage_data, options):
        """Get text output from the SummaryReporter."""
        cov = control.Coverage()
        cov.data = coverage_data
        printer = summary.SummaryReporter(cov, options)
        destination = StringIO()
        printer.report([], destination)
        return destination.getvalue()

    if sys.version_info < (2, 7):
        def assertNotIn(self, needle, haystack):
            self.assertTrue(needle not in haystack)

    def test_defaults(self):
        """Run the report with no configuration options."""
        data = self.get_coverage_data()
        opts = config.CoverageConfig()
        report = self.get_summary_text(data, opts)
        self.assertNotIn('Missing', report)
        self.assertNotIn('Branch', report)

    def test_print_missing(self):
        """Run the report printing the missing lines."""
        data = self.get_coverage_data()
        opts = config.CoverageConfig()
        opts.from_args(show_missing=True)
        report = self.get_summary_text(data, opts)
        if sys.version_info > (2, 7):
            self.assertIn('Missing', report)
        else:
            self.assertTrue('Missing' in report)
        self.assertNotIn('Branch', report)

    def test_sort_report(self):
        """Sort the text report."""
        data = self.get_coverage_data()
        opts = config.CoverageConfig()
        opts.from_args(sort='Stmts')
        report = self.get_summary_text(data, opts)
        # just the basename, to avoid pyc and directory name complexities
        filename = os.path.splitext(os.path.basename(__file__))[0]
        location1 = report.find('helpers')
        location2 = report.find(filename)
        if sys.version_info > (2, 7):
            self.assertLess(location1, location2)
        else:
            self.assertTrue(location1 < location2)
