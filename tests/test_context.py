# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Tests for context support."""

import os.path

import coverage
from coverage import env
from coverage.data import CoverageData
from coverage.misc import CoverageException

from tests.coveragetest import CoverageTest


class StaticContextTest(CoverageTest):
    """Tests of the static context."""

    def setUp(self):
        super(StaticContextTest, self).setUp()
        self.skip_unless_data_storage_is("sql")

    def test_no_context(self):
        self.make_file("main.py", "a = 1")
        cov = coverage.Coverage()
        self.start_import_stop(cov, "main")
        data = cov.get_data()
        self.assertCountEqual(data.measured_contexts(), [""])

    def test_static_context(self):
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


class DynamicContextTest(CoverageTest):
    """Tests of dynamically changing contexts."""

    def setUp(self):
        super(DynamicContextTest, self).setUp()
        self.skip_unless_data_storage_is("sql")
        if not env.C_TRACER:
            self.skipTest("Only the C tracer supports dynamic contexts")

    def test_simple(self):
        self.make_file("two_tests.py", """\
            def helper(lineno):
                x = 2

            def test_one():
                a = 5
                helper(6)

            def test_two():
                a = 9
                b = 10
                if a > 11:
                    b = 12
                assert a == (13-4)
                assert b == (14-4)
                helper(15)

            test_one()
            x = 18
            helper(19)
            test_two()
            """)
        cov = coverage.Coverage(source=["."])
        cov.set_option("run:dynamic_context", "test_function")
        self.start_import_stop(cov, "two_tests")
        data = cov.get_data()

        fname = os.path.abspath("two_tests.py")
        self.assertCountEqual(data.measured_contexts(), ["", "test_one", "test_two"])
        self.assertCountEqual(data.lines(fname, ""), [1, 4, 8, 17, 18, 19, 2, 20])
        self.assertCountEqual(data.lines(fname, "test_one"), [5, 6, 2])
        self.assertCountEqual(data.lines(fname, "test_two"), [9, 10, 11, 13, 14, 15, 2])


class DynamicContextWithPythonTracerTest(CoverageTest):
    """The Python tracer doesn't do dynamic contexts at all."""

    run_in_temp_dir = False

    def test_python_tracer_fails_properly(self):
        if env.C_TRACER:
            self.skipTest("This test is specifically about the Python tracer.")
        cov = coverage.Coverage()
        cov.set_option("run:dynamic_context", "test_function")
        msg = r"Can't support dynamic contexts with PyTracer"
        with self.assertRaisesRegex(CoverageException, msg):
            cov.start()
