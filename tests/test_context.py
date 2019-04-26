# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Tests for context support."""

import inspect
import os.path

import coverage
from coverage import env
from coverage.context import qualname_from_frame
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
        if not env.C_TRACER:
            self.skipTest("Only the C tracer supports dynamic contexts")
        super(DynamicContextTest, self).setUp()
        self.skip_unless_data_storage_is("sql")

    SOURCE = """\
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
        """

    OUTER_LINES = [1, 4, 8, 17, 18, 19, 2, 20]
    TEST_ONE_LINES = [5, 6, 2]
    TEST_TWO_LINES = [9, 10, 11, 13, 14, 15, 2]

    def test_dynamic_alone(self):
        self.make_file("two_tests.py", self.SOURCE)
        cov = coverage.Coverage(source=["."])
        cov.set_option("run:dynamic_context", "test_function")
        self.start_import_stop(cov, "two_tests")
        data = cov.get_data()

        full_names = {os.path.basename(f): f for f in data.measured_files()}
        fname = full_names["two_tests.py"]
        self.assertCountEqual(data.measured_contexts(), ["", "test_one", "test_two"])
        self.assertCountEqual(data.lines(fname, ""), self.OUTER_LINES)
        self.assertCountEqual(data.lines(fname, "test_one"), self.TEST_ONE_LINES)
        self.assertCountEqual(data.lines(fname, "test_two"), self.TEST_TWO_LINES)

    def test_static_and_dynamic(self):
        self.make_file("two_tests.py", self.SOURCE)
        cov = coverage.Coverage(context="stat", source=["."])
        cov.set_option("run:dynamic_context", "test_function")
        self.start_import_stop(cov, "two_tests")
        data = cov.get_data()

        full_names = {os.path.basename(f): f for f in data.measured_files()}
        fname = full_names["two_tests.py"]
        self.assertCountEqual(data.measured_contexts(), ["stat", "stat|test_one", "stat|test_two"])
        self.assertCountEqual(data.lines(fname, "stat"), self.OUTER_LINES)
        self.assertCountEqual(data.lines(fname, "stat|test_one"), self.TEST_ONE_LINES)
        self.assertCountEqual(data.lines(fname, "stat|test_two"), self.TEST_TWO_LINES)


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


def get_qualname():
    """Helper to return qualname_from_frame for the caller."""
    stack = inspect.stack()[1:]
    if any(sinfo[0].f_code.co_name == "get_qualname" for sinfo in stack):
        # We're calling outselves recursively, maybe because we're testing
        # properties. Return an int to try to get back on track.
        return 17
    caller_frame = stack[0][0]
    return qualname_from_frame(caller_frame)

# pylint: disable=missing-docstring, unused-argument

class Parent(object):
    def meth(self):
        return get_qualname()

    @property
    def a_property(self):
        return get_qualname()

class Child(Parent):
    pass

class SomethingElse(object):
    pass

class MultiChild(SomethingElse, Child):
    pass

def no_arguments():
    return get_qualname()

def plain_old_function(a, b):
    return get_qualname()

def fake_out(self):
    return get_qualname()

def patch_meth(self):
    return get_qualname()

class OldStyle:                         # pylint: disable=old-style-class
    def meth(self):
        return get_qualname()

class OldChild(OldStyle):
    pass

# pylint: enable=missing-docstring, unused-argument


class QualnameTest(CoverageTest):
    """Tests of qualname_from_frame."""

    # Pylint gets confused about meth() below.
    # pylint: disable=no-value-for-parameter

    run_in_temp_dir = False

    def test_method(self):
        self.assertEqual(Parent().meth(), "Parent.meth")

    def test_inherited_method(self):
        self.assertEqual(Child().meth(), "Parent.meth")

    def test_mi_inherited_method(self):
        self.assertEqual(MultiChild().meth(), "Parent.meth")

    def test_no_arguments(self):
        self.assertEqual(no_arguments(), "no_arguments")

    def test_plain_old_function(self):
        self.assertEqual(plain_old_function(0, 1), "plain_old_function")

    def test_fake_out(self):
        self.assertEqual(fake_out(0), "fake_out")

    def test_property(self):
        # I'd like this to be "Parent.a_property", but this might be ok too.
        self.assertEqual(Parent().a_property, "a_property")

    def test_changeling(self):
        c = Child()
        c.meth = patch_meth
        self.assertEqual(c.meth(c), "patch_meth")

    def test_oldstyle(self):
        if not env.PY2:
            self.skipTest("Old-style classes are only in Python 2")
        self.assertEqual(OldStyle().meth(), "meth")
        self.assertEqual(OldChild().meth(), "meth")
