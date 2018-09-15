# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Tests for context support."""

import coverage

from tests.coveragetest import CoverageTest


class GlobalContextTest(CoverageTest):
    """Tests of the global context."""

    def setUp(self):
        super(GlobalContextTest, self).setUp()
        self.skip_unless_data_storage_is("sql")

    def test_no_context(self):
        self.make_file("main.py", "a = 1")
        cov = coverage.Coverage()
        self.start_import_stop(cov, "main")
        data = cov.get_data()
        self.assertCountEqual(data.measured_contexts(), [""])

    def test_global_context(self):
        self.make_file("main.py", "a = 1")
        cov = coverage.Coverage(context="gooey")
        self.start_import_stop(cov, "main")
        data = cov.get_data()
        self.assertCountEqual(data.measured_contexts(), ["gooey"])
