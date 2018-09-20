# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Tests for context support."""

import os.path

import coverage
from coverage.data import CoverageData

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

    SOURCE = """\
        a = 1
        if a > 2:
            a = 3
        assert a == 1
        """

    LINES = [1, 2, 4]
    ARCS = [(-1, 1), (1, 2), (2, 4), (4, -1)]

    def run_red_blue(self, **options):
        """Run red.py and blue.py, and return their CoverageData objects."""
        self.make_file("red.py", self.SOURCE)
        red_cov = coverage.Coverage(context="red", data_suffix="r", source=["."], **options)
        self.start_import_stop(red_cov, "red")
        red_cov.save()
        red_data = red_cov.get_data()

        self.make_file("blue.py", self.SOURCE)
        blue_cov = coverage.Coverage(context="blue", data_suffix="b", source=["."], **options)
        self.start_import_stop(blue_cov, "blue")
        blue_cov.save()
        blue_data = blue_cov.get_data()

        return red_data, blue_data

    def test_combining_line_contexts(self):
        red_data, blue_data = self.run_red_blue()
        for datas in [[red_data, blue_data], [blue_data, red_data]]:
            combined = CoverageData(suffix="combined")
            for data in datas:
                combined.update(data)

            self.assertEqual(combined.measured_contexts(), {'red', 'blue'})

            full_names = {os.path.basename(f): f for f in combined.measured_files()}
            self.assertCountEqual(full_names, ['red.py', 'blue.py'])

            fred = full_names['red.py']
            fblue = full_names['blue.py']

            self.assertEqual(combined.lines(fred, context='red'), self.LINES)
            self.assertEqual(combined.lines(fred, context='blue'), [])
            self.assertEqual(combined.lines(fblue, context='red'), [])
            self.assertEqual(combined.lines(fblue, context='blue'), self.LINES)

    def test_combining_arc_contexts(self):
        red_data, blue_data = self.run_red_blue(branch=True)
        for datas in [[red_data, blue_data], [blue_data, red_data]]:
            combined = CoverageData(suffix="combined")
            for data in datas:
                combined.update(data)

            self.assertEqual(combined.measured_contexts(), {'red', 'blue'})

            full_names = {os.path.basename(f): f for f in combined.measured_files()}
            self.assertCountEqual(full_names, ['red.py', 'blue.py'])

            fred = full_names['red.py']
            fblue = full_names['blue.py']

            self.assertEqual(combined.lines(fred, context='red'), self.LINES)
            self.assertEqual(combined.lines(fred, context='blue'), [])
            self.assertEqual(combined.lines(fblue, context='red'), [])
            self.assertEqual(combined.lines(fblue, context='blue'), self.LINES)

            self.assertEqual(combined.arcs(fred, context='red'), self.ARCS)
            self.assertEqual(combined.arcs(fred, context='blue'), [])
            self.assertEqual(combined.arcs(fblue, context='red'), [])
            self.assertEqual(combined.arcs(fblue, context='blue'), self.ARCS)
