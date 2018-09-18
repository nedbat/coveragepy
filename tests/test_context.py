# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Tests for context support."""

import os.path

import coverage
from coverage.data import CoverageData, combine_parallel_data

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

    def run_red_blue(self, **options):
        self.make_file("red.py", """\
            a = 1
            if a > 2:
                a = 3
            assert a == 1
            """)
        red_cov = coverage.Coverage(context="red", data_suffix="r", source=["."], **options)
        self.start_import_stop(red_cov, "red")
        red_cov.save()

        self.make_file("blue.py", """\
            b = 1
            if b > 2:
                b = 3
            assert b == 1
            """)
        blue_cov = coverage.Coverage(context="blue", data_suffix="b", source=["."], **options)
        self.start_import_stop(blue_cov, "blue")
        blue_cov.save()

    def test_combining_line_contexts(self):
        self.run_red_blue()
        combined = CoverageData()
        combine_parallel_data(combined)

        self.assertEqual(combined.measured_contexts(), {'red', 'blue'})

        full_names = {os.path.basename(f): f for f in combined.measured_files()}
        self.assertCountEqual(full_names, ['red.py', 'blue.py'])

        self.assertEqual(combined.lines(full_names['red.py'], context='red'), [1, 2, 4])
        self.assertEqual(combined.lines(full_names['red.py'], context='blue'), [])
        self.assertEqual(combined.lines(full_names['blue.py'], context='red'), [])
        self.assertEqual(combined.lines(full_names['blue.py'], context='blue'), [1, 2, 4])

    def test_combining_arc_contexts(self):
        self.run_red_blue(branch=True)
        combined = CoverageData()
        combine_parallel_data(combined)

        self.assertEqual(combined.measured_contexts(), {'red', 'blue'})

        full_names = {os.path.basename(f): f for f in combined.measured_files()}
        self.assertCountEqual(full_names, ['red.py', 'blue.py'])

        self.assertEqual(combined.lines(full_names['red.py'], context='red'), [1, 2, 4])
        self.assertEqual(combined.lines(full_names['red.py'], context='blue'), [])
        self.assertEqual(combined.lines(full_names['blue.py'], context='red'), [])
        self.assertEqual(combined.lines(full_names['blue.py'], context='blue'), [1, 2, 4])

        self.assertEqual(combined.arcs(full_names['red.py'], context='red'), [(-1, 1), (1, 2), (2, 4), (4, -1)])
        self.assertEqual(combined.arcs(full_names['red.py'], context='blue'), [])
        self.assertEqual(combined.arcs(full_names['blue.py'], context='red'), [])
        self.assertEqual(combined.arcs(full_names['blue.py'], context='blue'), [(-1, 1), (1, 2), (2, 4), (4, -1)])
