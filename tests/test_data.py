# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Tests for coverage.data"""

import glob
import os
import os.path
import re
import sqlite3
import threading

import mock
import pytest

from coverage.data import CoverageData, combine_parallel_data
from coverage.data import add_data_to_hash, line_counts
from coverage.debug import DebugControlString
from coverage.files import PathAliases, canonical_filename
from coverage.misc import CoverageException

from tests.coveragetest import CoverageTest
from tests.helpers import assert_count_equal


LINES_1 = {
    'a.py': {1: None, 2: None},
    'b.py': {3: None},
}
SUMMARY_1 = {'a.py': 2, 'b.py': 1}
MEASURED_FILES_1 = ['a.py', 'b.py']
A_PY_LINES_1 = [1, 2]
B_PY_LINES_1 = [3]

LINES_2 = {
    'a.py': {1: None, 5: None},
    'c.py': {17: None},
}
SUMMARY_1_2 = {'a.py': 3, 'b.py': 1, 'c.py': 1}
MEASURED_FILES_1_2 = ['a.py', 'b.py', 'c.py']

ARCS_3 = {
    'x.py': {
        (-1, 1): None,
        (1, 2): None,
        (2, 3): None,
        (3, -1): None,
    },
    'y.py': {
        (-1, 17): None,
        (17, 23): None,
        (23, -1): None,
    },
}
X_PY_ARCS_3 = [(-1, 1), (1, 2), (2, 3), (3, -1)]
Y_PY_ARCS_3 = [(-1, 17), (17, 23), (23, -1)]
SUMMARY_3 = {'x.py': 3, 'y.py': 2}
MEASURED_FILES_3 = ['x.py', 'y.py']
X_PY_LINES_3 = [1, 2, 3]
Y_PY_LINES_3 = [17, 23]

ARCS_4 = {
    'x.py': {
        (-1, 2): None,
        (2, 5): None,
        (5, -1): None,
    },
    'z.py': {
        (-1, 1000): None,
        (1000, -1): None,
    },
}
SUMMARY_3_4 = {'x.py': 4, 'y.py': 2, 'z.py': 1}
MEASURED_FILES_3_4 = ['x.py', 'y.py', 'z.py']


class DataTestHelpers(CoverageTest):
    """Test helpers for data tests."""

    def assert_line_counts(self, covdata, counts, fullpath=False):
        """Check that the line_counts of `covdata` is `counts`."""
        assert line_counts(covdata, fullpath) == counts

    def assert_measured_files(self, covdata, measured):
        """Check that `covdata`'s measured files are `measured`."""
        assert_count_equal(covdata.measured_files(), measured)

    def assert_lines1_data(self, covdata):
        """Check that `covdata` has the data from LINES1."""
        self.assert_line_counts(covdata, SUMMARY_1)
        self.assert_measured_files(covdata, MEASURED_FILES_1)
        assert_count_equal(covdata.lines("a.py"), A_PY_LINES_1)
        assert not covdata.has_arcs()

    def assert_arcs3_data(self, covdata):
        """Check that `covdata` has the data from ARCS3."""
        self.assert_line_counts(covdata, SUMMARY_3)
        self.assert_measured_files(covdata, MEASURED_FILES_3)
        assert_count_equal(covdata.lines("x.py"), X_PY_LINES_3)
        assert_count_equal(covdata.arcs("x.py"), X_PY_ARCS_3)
        assert_count_equal(covdata.lines("y.py"), Y_PY_LINES_3)
        assert_count_equal(covdata.arcs("y.py"), Y_PY_ARCS_3)
        assert covdata.has_arcs()


class CoverageDataTest(DataTestHelpers, CoverageTest):
    """Test cases for CoverageData."""

    no_files_in_temp_dir = True

    def test_empty_data_is_false(self):
        covdata = CoverageData()
        assert not covdata

    def test_line_data_is_true(self):
        covdata = CoverageData()
        covdata.add_lines(LINES_1)
        assert covdata

    def test_arc_data_is_true(self):
        covdata = CoverageData()
        covdata.add_arcs(ARCS_3)
        assert covdata

    def test_empty_line_data_is_false(self):
        covdata = CoverageData()
        covdata.add_lines({})
        assert not covdata

    def test_empty_arc_data_is_false(self):
        covdata = CoverageData()
        covdata.add_arcs({})
        assert not covdata

    def test_adding_lines(self):
        covdata = CoverageData()
        covdata.add_lines(LINES_1)
        self.assert_lines1_data(covdata)

    def test_adding_arcs(self):
        covdata = CoverageData()
        covdata.add_arcs(ARCS_3)
        self.assert_arcs3_data(covdata)

    def test_ok_to_add_lines_twice(self):
        covdata = CoverageData()
        covdata.add_lines(LINES_1)
        covdata.add_lines(LINES_2)
        self.assert_line_counts(covdata, SUMMARY_1_2)
        self.assert_measured_files(covdata, MEASURED_FILES_1_2)

    def test_ok_to_add_arcs_twice(self):
        covdata = CoverageData()
        covdata.add_arcs(ARCS_3)
        covdata.add_arcs(ARCS_4)
        self.assert_line_counts(covdata, SUMMARY_3_4)
        self.assert_measured_files(covdata, MEASURED_FILES_3_4)

    def test_cant_add_arcs_with_lines(self):
        covdata = CoverageData()
        covdata.add_lines(LINES_1)
        msg = "Can't add branch measurements to existing line data"
        with pytest.raises(CoverageException, match=msg):
            covdata.add_arcs(ARCS_3)

    def test_cant_add_lines_with_arcs(self):
        covdata = CoverageData()
        covdata.add_arcs(ARCS_3)
        msg = "Can't add line measurements to existing branch data"
        with pytest.raises(CoverageException, match=msg):
            covdata.add_lines(LINES_1)

    def test_touch_file_with_lines(self):
        covdata = CoverageData()
        covdata.add_lines(LINES_1)
        covdata.touch_file('zzz.py')
        self.assert_measured_files(covdata, MEASURED_FILES_1 + ['zzz.py'])

    def test_touch_file_with_arcs(self):
        covdata = CoverageData()
        covdata.add_arcs(ARCS_3)
        covdata.touch_file('zzz.py')
        self.assert_measured_files(covdata, MEASURED_FILES_3 + ['zzz.py'])

    def test_set_query_contexts(self):
        covdata = CoverageData()
        covdata.set_context('test_a')
        covdata.add_lines(LINES_1)
        covdata.set_query_contexts(['test_*'])
        assert covdata.lines('a.py') == [1, 2]
        covdata.set_query_contexts(['other*'])
        assert covdata.lines('a.py') == []

    def test_no_lines_vs_unmeasured_file(self):
        covdata = CoverageData()
        covdata.add_lines(LINES_1)
        covdata.touch_file('zzz.py')
        assert covdata.lines('zzz.py') == []
        assert covdata.lines('no_such_file.py') is None

    def test_lines_with_contexts(self):
        covdata = CoverageData()
        covdata.set_context('test_a')
        covdata.add_lines(LINES_1)
        assert covdata.lines('a.py') == [1, 2]
        covdata.set_query_contexts(['test*'])
        assert covdata.lines('a.py') == [1, 2]
        covdata.set_query_contexts(['other*'])
        assert covdata.lines('a.py') == []

    def test_contexts_by_lineno_with_lines(self):
        covdata = CoverageData()
        covdata.set_context('test_a')
        covdata.add_lines(LINES_1)
        assert covdata.contexts_by_lineno('a.py') == {1: ['test_a'], 2: ['test_a']}

    def test_no_duplicate_lines(self):
        covdata = CoverageData()
        covdata.set_context("context1")
        covdata.add_lines(LINES_1)
        covdata.set_context("context2")
        covdata.add_lines(LINES_1)
        assert covdata.lines('a.py') == A_PY_LINES_1

    def test_no_duplicate_arcs(self):
        covdata = CoverageData()
        covdata.set_context("context1")
        covdata.add_arcs(ARCS_3)
        covdata.set_context("context2")
        covdata.add_arcs(ARCS_3)
        assert covdata.arcs('x.py') == X_PY_ARCS_3

    def test_no_arcs_vs_unmeasured_file(self):
        covdata = CoverageData()
        covdata.add_arcs(ARCS_3)
        covdata.touch_file('zzz.py')
        assert covdata.lines('zzz.py') == []
        assert covdata.lines('no_such_file.py') is None
        assert covdata.arcs('zzz.py') == []
        assert covdata.arcs('no_such_file.py') is None

    def test_arcs_with_contexts(self):
        covdata = CoverageData()
        covdata.set_context('test_x')
        covdata.add_arcs(ARCS_3)
        assert covdata.arcs('x.py') == [(-1, 1), (1, 2), (2, 3), (3, -1)]
        covdata.set_query_contexts(['test*'])
        assert covdata.arcs('x.py') == [(-1, 1), (1, 2), (2, 3), (3, -1)]
        covdata.set_query_contexts(['other*'])
        assert covdata.arcs('x.py') == []

    def test_contexts_by_lineno_with_arcs(self):
        covdata = CoverageData()
        covdata.set_context('test_x')
        covdata.add_arcs(ARCS_3)
        expected = {-1: ['test_x'], 1: ['test_x'], 2: ['test_x'], 3: ['test_x']}
        assert expected == covdata.contexts_by_lineno('x.py')

    def test_contexts_by_lineno_with_unknown_file(self):
        covdata = CoverageData()
        assert covdata.contexts_by_lineno('xyz.py') == {}

    def test_file_tracer_name(self):
        covdata = CoverageData()
        covdata.add_lines({
            "p1.foo": dict.fromkeys([1, 2, 3]),
            "p2.html": dict.fromkeys([10, 11, 12]),
            "main.py": dict.fromkeys([20]),
        })
        covdata.add_file_tracers({"p1.foo": "p1.plugin", "p2.html": "p2.plugin"})
        assert covdata.file_tracer("p1.foo") == "p1.plugin"
        assert covdata.file_tracer("main.py") == ""
        assert covdata.file_tracer("p3.not_here") is None

    def test_cant_file_tracer_unmeasured_files(self):
        covdata = CoverageData()
        msg = "Can't add file tracer data for unmeasured file 'p1.foo'"
        with pytest.raises(CoverageException, match=msg):
            covdata.add_file_tracers({"p1.foo": "p1.plugin"})

        covdata.add_lines({"p2.html": dict.fromkeys([10, 11, 12])})
        with pytest.raises(CoverageException, match=msg):
            covdata.add_file_tracers({"p1.foo": "p1.plugin"})

    def test_cant_change_file_tracer_name(self):
        covdata = CoverageData()
        covdata.add_lines({"p1.foo": dict.fromkeys([1, 2, 3])})
        covdata.add_file_tracers({"p1.foo": "p1.plugin"})

        msg = "Conflicting file tracer name for 'p1.foo': u?'p1.plugin' vs u?'p1.plugin.foo'"
        with pytest.raises(CoverageException, match=msg):
            covdata.add_file_tracers({"p1.foo": "p1.plugin.foo"})

    def test_update_lines(self):
        covdata1 = CoverageData(suffix='1')
        covdata1.add_lines(LINES_1)

        covdata2 = CoverageData(suffix='2')
        covdata2.add_lines(LINES_2)

        covdata3 = CoverageData(suffix='3')
        covdata3.update(covdata1)
        covdata3.update(covdata2)

        self.assert_line_counts(covdata3, SUMMARY_1_2)
        self.assert_measured_files(covdata3, MEASURED_FILES_1_2)

    def test_update_arcs(self):
        covdata1 = CoverageData(suffix='1')
        covdata1.add_arcs(ARCS_3)

        covdata2 = CoverageData(suffix='2')
        covdata2.add_arcs(ARCS_4)

        covdata3 = CoverageData(suffix='3')
        covdata3.update(covdata1)
        covdata3.update(covdata2)

        self.assert_line_counts(covdata3, SUMMARY_3_4)
        self.assert_measured_files(covdata3, MEASURED_FILES_3_4)

    def test_update_cant_mix_lines_and_arcs(self):
        covdata1 = CoverageData(suffix='1')
        covdata1.add_lines(LINES_1)

        covdata2 = CoverageData(suffix='2')
        covdata2.add_arcs(ARCS_3)

        with pytest.raises(CoverageException, match="Can't combine arc data with line data"):
            covdata1.update(covdata2)

        with pytest.raises(CoverageException, match="Can't combine line data with arc data"):
            covdata2.update(covdata1)

    def test_update_file_tracers(self):
        covdata1 = CoverageData(suffix='1')
        covdata1.add_lines({
            "p1.html": dict.fromkeys([1, 2, 3, 4]),
            "p2.html": dict.fromkeys([5, 6, 7]),
            "main.py": dict.fromkeys([10, 11, 12]),
        })
        covdata1.add_file_tracers({
            "p1.html": "html.plugin",
            "p2.html": "html.plugin2",
        })

        covdata2 = CoverageData(suffix='2')
        covdata2.add_lines({
            "p1.html": dict.fromkeys([3, 4, 5, 6]),
            "p2.html": dict.fromkeys([7, 8, 9]),
            "p3.foo": dict.fromkeys([1000, 1001]),
            "main.py": dict.fromkeys([10, 11, 12]),
        })
        covdata2.add_file_tracers({
            "p1.html": "html.plugin",
            "p2.html": "html.plugin2",
            "p3.foo": "foo_plugin",
        })

        covdata3 = CoverageData(suffix='3')
        covdata3.update(covdata1)
        covdata3.update(covdata2)
        assert covdata3.file_tracer("p1.html") == "html.plugin"
        assert covdata3.file_tracer("p2.html") == "html.plugin2"
        assert covdata3.file_tracer("p3.foo") == "foo_plugin"
        assert covdata3.file_tracer("main.py") == ""

    def test_update_conflicting_file_tracers(self):
        covdata1 = CoverageData(suffix='1')
        covdata1.add_lines({"p1.html": dict.fromkeys([1, 2, 3])})
        covdata1.add_file_tracers({"p1.html": "html.plugin"})

        covdata2 = CoverageData(suffix='2')
        covdata2.add_lines({"p1.html": dict.fromkeys([1, 2, 3])})
        covdata2.add_file_tracers({"p1.html": "html.other_plugin"})

        msg = "Conflicting file tracer name for 'p1.html': u?'html.plugin' vs u?'html.other_plugin'"
        with pytest.raises(CoverageException, match=msg):
            covdata1.update(covdata2)

        msg = "Conflicting file tracer name for 'p1.html': u?'html.other_plugin' vs u?'html.plugin'"
        with pytest.raises(CoverageException, match=msg):
            covdata2.update(covdata1)

    def test_update_file_tracer_vs_no_file_tracer(self):
        covdata1 = CoverageData(suffix="1")
        covdata1.add_lines({"p1.html": dict.fromkeys([1, 2, 3])})
        covdata1.add_file_tracers({"p1.html": "html.plugin"})

        covdata2 = CoverageData(suffix="2")
        covdata2.add_lines({"p1.html": dict.fromkeys([1, 2, 3])})

        msg = "Conflicting file tracer name for 'p1.html': u?'html.plugin' vs u?''"
        with pytest.raises(CoverageException, match=msg):
            covdata1.update(covdata2)

        msg = "Conflicting file tracer name for 'p1.html': u?'' vs u?'html.plugin'"
        with pytest.raises(CoverageException, match=msg):
            covdata2.update(covdata1)

    def test_update_lines_empty(self):
        covdata1 = CoverageData(suffix='1')
        covdata1.add_lines(LINES_1)

        covdata2 = CoverageData(suffix='2')
        covdata1.update(covdata2)
        self.assert_line_counts(covdata1, SUMMARY_1)

    def test_update_arcs_empty(self):
        covdata1 = CoverageData(suffix='1')
        covdata1.add_arcs(ARCS_3)

        covdata2 = CoverageData(suffix='2')
        covdata1.update(covdata2)
        self.assert_line_counts(covdata1, SUMMARY_3)

    def test_asking_isnt_measuring(self):
        # Asking about an unmeasured file shouldn't make it seem measured.
        covdata = CoverageData()
        self.assert_measured_files(covdata, [])
        assert covdata.arcs("missing.py") is None
        self.assert_measured_files(covdata, [])

    def test_add_to_hash_with_lines(self):
        covdata = CoverageData()
        covdata.add_lines(LINES_1)
        hasher = mock.Mock()
        add_data_to_hash(covdata, "a.py", hasher)
        assert hasher.method_calls == [
            mock.call.update([1, 2]),   # lines
            mock.call.update(""),       # file_tracer name
        ]

    def test_add_to_hash_with_arcs(self):
        covdata = CoverageData()
        covdata.add_arcs(ARCS_3)
        covdata.add_file_tracers({"y.py": "hologram_plugin"})
        hasher = mock.Mock()
        add_data_to_hash(covdata, "y.py", hasher)
        assert hasher.method_calls == [
            mock.call.update([(-1, 17), (17, 23), (23, -1)]),   # arcs
            mock.call.update("hologram_plugin"),                # file_tracer name
        ]

    def test_add_to_lines_hash_with_missing_file(self):
        # https://github.com/nedbat/coveragepy/issues/403
        covdata = CoverageData()
        covdata.add_lines(LINES_1)
        hasher = mock.Mock()
        add_data_to_hash(covdata, "missing.py", hasher)
        assert hasher.method_calls == [
            mock.call.update([]),
            mock.call.update(None),
        ]

    def test_add_to_arcs_hash_with_missing_file(self):
        # https://github.com/nedbat/coveragepy/issues/403
        covdata = CoverageData()
        covdata.add_arcs(ARCS_3)
        covdata.add_file_tracers({"y.py": "hologram_plugin"})
        hasher = mock.Mock()
        add_data_to_hash(covdata, "missing.py", hasher)
        assert hasher.method_calls == [
            mock.call.update([]),
            mock.call.update(None),
        ]

    def test_empty_lines_are_still_lines(self):
        covdata = CoverageData()
        covdata.add_lines({})
        covdata.touch_file("abc.py")
        assert not covdata.has_arcs()

    def test_empty_arcs_are_still_arcs(self):
        covdata = CoverageData()
        covdata.add_arcs({})
        covdata.touch_file("abc.py")
        assert covdata.has_arcs()

    def test_read_and_write_are_opposites(self):
        covdata1 = CoverageData()
        covdata1.add_arcs(ARCS_3)
        covdata1.write()

        covdata2 = CoverageData()
        covdata2.read()
        self.assert_arcs3_data(covdata2)

    def test_thread_stress(self):
        covdata = CoverageData()

        def thread_main():
            """Every thread will try to add the same data."""
            covdata.add_lines(LINES_1)

        threads = [threading.Thread(target=thread_main) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assert_lines1_data(covdata)


class CoverageDataTestInTempDir(DataTestHelpers, CoverageTest):
    """Tests of CoverageData that need a temporary directory to make files."""

    def test_read_write_lines(self):
        covdata1 = CoverageData("lines.dat")
        covdata1.add_lines(LINES_1)
        covdata1.write()

        covdata2 = CoverageData("lines.dat")
        covdata2.read()
        self.assert_lines1_data(covdata2)

    def test_read_write_arcs(self):
        covdata1 = CoverageData("arcs.dat")
        covdata1.add_arcs(ARCS_3)
        covdata1.write()

        covdata2 = CoverageData("arcs.dat")
        covdata2.read()
        self.assert_arcs3_data(covdata2)

    def test_read_errors(self):
        msg = r"Couldn't .* '.*[/\\]{0}': \S+"

        self.make_file("xyzzy.dat", "xyzzy")
        with pytest.raises(CoverageException, match=msg.format("xyzzy.dat")):
            covdata = CoverageData("xyzzy.dat")
            covdata.read()
        assert not covdata

        self.make_file("empty.dat", "")
        with pytest.raises(CoverageException, match=msg.format("empty.dat")):
            covdata = CoverageData("empty.dat")
            covdata.read()
        assert not covdata

    def test_read_sql_errors(self):
        with sqlite3.connect("wrong_schema.db") as con:
            con.execute("create table coverage_schema (version integer)")
            con.execute("insert into coverage_schema (version) values (99)")
        msg = r"Couldn't .* '.*[/\\]{}': wrong schema: 99 instead of \d+".format("wrong_schema.db")
        with pytest.raises(CoverageException, match=msg):
            covdata = CoverageData("wrong_schema.db")
            covdata.read()
        assert not covdata

        with sqlite3.connect("no_schema.db") as con:
            con.execute("create table foobar (baz text)")
        msg = r"Couldn't .* '.*[/\\]{}': \S+".format("no_schema.db")
        with pytest.raises(CoverageException, match=msg):
            covdata = CoverageData("no_schema.db")
            covdata.read()
        assert not covdata


class CoverageDataFilesTest(DataTestHelpers, CoverageTest):
    """Tests of CoverageData file handling."""

    no_files_in_temp_dir = True

    def test_reading_missing(self):
        self.assert_doesnt_exist(".coverage")
        covdata = CoverageData()
        covdata.read()
        self.assert_line_counts(covdata, {})

    def test_writing_and_reading(self):
        covdata1 = CoverageData()
        covdata1.add_lines(LINES_1)
        covdata1.write()

        covdata2 = CoverageData()
        covdata2.read()
        self.assert_line_counts(covdata2, SUMMARY_1)

    def test_debug_output_with_debug_option(self):
        # With debug option dataio, we get debug output about reading and
        # writing files.
        debug = DebugControlString(options=["dataio"])
        covdata1 = CoverageData(debug=debug)
        covdata1.add_lines(LINES_1)
        covdata1.write()

        covdata2 = CoverageData(debug=debug)
        covdata2.read()
        self.assert_line_counts(covdata2, SUMMARY_1)

        assert re.search(
            r"^Erasing data file '.*\.coverage'\n"
            r"Creating data file '.*\.coverage'\n"
            r"Opening data file '.*\.coverage'\n$",
            debug.get_output()
        )

    def test_debug_output_without_debug_option(self):
        # With a debug object, but not the dataio option, we don't get debug
        # output.
        debug = DebugControlString(options=[])
        covdata1 = CoverageData(debug=debug)
        covdata1.add_lines(LINES_1)
        covdata1.write()

        covdata2 = CoverageData(debug=debug)
        covdata2.read()
        self.assert_line_counts(covdata2, SUMMARY_1)

        assert debug.get_output() == ""

    def test_explicit_suffix(self):
        self.assert_doesnt_exist(".coverage.SUFFIX")
        covdata = CoverageData(suffix='SUFFIX')
        covdata.add_lines(LINES_1)
        covdata.write()
        self.assert_exists(".coverage.SUFFIX")
        self.assert_doesnt_exist(".coverage")

    def test_true_suffix(self):
        self.assert_file_count(".coverage.*", 0)

        # suffix=True will make a randomly named data file.
        covdata1 = CoverageData(suffix=True)
        covdata1.add_lines(LINES_1)
        covdata1.write()
        self.assert_doesnt_exist(".coverage")
        data_files1 = glob.glob(".coverage.*")
        assert len(data_files1) == 1

        # Another suffix=True will choose a different name.
        covdata2 = CoverageData(suffix=True)
        covdata2.add_lines(LINES_1)
        covdata2.write()
        self.assert_doesnt_exist(".coverage")
        data_files2 = glob.glob(".coverage.*")
        assert len(data_files2) == 2

        # In addition to being different, the suffixes have the pid in them.
        assert all(str(os.getpid()) in fn for fn in data_files2)

    def test_combining(self):
        self.assert_file_count(".coverage.*", 0)

        covdata1 = CoverageData(suffix='1')
        covdata1.add_lines(LINES_1)
        covdata1.write()
        self.assert_exists(".coverage.1")
        self.assert_file_count(".coverage.*", 1)

        covdata2 = CoverageData(suffix='2')
        covdata2.add_lines(LINES_2)
        covdata2.write()
        self.assert_exists(".coverage.2")
        self.assert_file_count(".coverage.*", 2)

        covdata3 = CoverageData()
        combine_parallel_data(covdata3)
        self.assert_line_counts(covdata3, SUMMARY_1_2)
        self.assert_measured_files(covdata3, MEASURED_FILES_1_2)
        self.assert_file_count(".coverage.*", 0)

    def test_erasing(self):
        covdata1 = CoverageData()
        covdata1.add_lines(LINES_1)
        covdata1.write()

        covdata1.erase()
        self.assert_line_counts(covdata1, {})

        covdata2 = CoverageData()
        covdata2.read()
        self.assert_line_counts(covdata2, {})

    def test_erasing_parallel(self):
        self.make_file("datafile.1")
        self.make_file("datafile.2")
        self.make_file(".coverage")
        data = CoverageData("datafile")
        data.erase(parallel=True)
        self.assert_file_count("datafile.*", 0)
        self.assert_exists(".coverage")

    def test_combining_with_aliases(self):
        covdata1 = CoverageData(suffix='1')
        covdata1.add_lines({
            '/home/ned/proj/src/a.py': {1: None, 2: None},
            '/home/ned/proj/src/sub/b.py': {3: None},
            '/home/ned/proj/src/template.html': {10: None},
        })
        covdata1.add_file_tracers({
            '/home/ned/proj/src/template.html': 'html.plugin',
        })
        covdata1.write()

        covdata2 = CoverageData(suffix='2')
        covdata2.add_lines({
            r'c:\ned\test\a.py': {4: None, 5: None},
            r'c:\ned\test\sub\b.py': {3: None, 6: None},
        })
        covdata2.write()

        self.assert_file_count(".coverage.*", 2)

        covdata3 = CoverageData()
        aliases = PathAliases()
        aliases.add("/home/ned/proj/src/", "./")
        aliases.add(r"c:\ned\test", "./")
        combine_parallel_data(covdata3, aliases=aliases)
        self.assert_file_count(".coverage.*", 0)
        # covdata3 hasn't been written yet. Should this file exist or not?
        #self.assert_exists(".coverage")

        apy = canonical_filename('./a.py')
        sub_bpy = canonical_filename('./sub/b.py')
        template_html = canonical_filename('./template.html')

        self.assert_line_counts(covdata3, {apy: 4, sub_bpy: 2, template_html: 1}, fullpath=True)
        self.assert_measured_files(covdata3, [apy, sub_bpy, template_html])
        assert covdata3.file_tracer(template_html) == 'html.plugin'

    def test_combining_from_different_directories(self):
        os.makedirs('cov1')
        covdata1 = CoverageData('cov1/.coverage.1')
        covdata1.add_lines(LINES_1)
        covdata1.write()

        os.makedirs('cov2')
        covdata2 = CoverageData('cov2/.coverage.2')
        covdata2.add_lines(LINES_2)
        covdata2.write()

        # This data won't be included.
        covdata_xxx = CoverageData('.coverage.xxx')
        covdata_xxx.add_arcs(ARCS_3)
        covdata_xxx.write()

        covdata3 = CoverageData()
        combine_parallel_data(covdata3, data_paths=['cov1', 'cov2'])

        self.assert_line_counts(covdata3, SUMMARY_1_2)
        self.assert_measured_files(covdata3, MEASURED_FILES_1_2)
        self.assert_doesnt_exist("cov1/.coverage.1")
        self.assert_doesnt_exist("cov2/.coverage.2")
        self.assert_exists(".coverage.xxx")

    def test_combining_from_files(self):
        os.makedirs('cov1')
        covdata1 = CoverageData('cov1/.coverage.1')
        covdata1.add_lines(LINES_1)
        covdata1.write()

        os.makedirs('cov2')
        covdata2 = CoverageData('cov2/.coverage.2')
        covdata2.add_lines(LINES_2)
        covdata2.write()

        # This data won't be included.
        covdata_xxx = CoverageData('.coverage.xxx')
        covdata_xxx.add_arcs(ARCS_3)
        covdata_xxx.write()

        covdata_2xxx = CoverageData('cov2/.coverage.xxx')
        covdata_2xxx.add_arcs(ARCS_3)
        covdata_2xxx.write()

        covdata3 = CoverageData()
        combine_parallel_data(covdata3, data_paths=['cov1', 'cov2/.coverage.2'])

        self.assert_line_counts(covdata3, SUMMARY_1_2)
        self.assert_measured_files(covdata3, MEASURED_FILES_1_2)
        self.assert_doesnt_exist("cov1/.coverage.1")
        self.assert_doesnt_exist("cov2/.coverage.2")
        self.assert_exists(".coverage.xxx")
        self.assert_exists("cov2/.coverage.xxx")

    def test_combining_from_nonexistent_directories(self):
        covdata = CoverageData()
        msg = "Couldn't combine from non-existent path 'xyzzy'"
        with pytest.raises(CoverageException, match=msg):
            combine_parallel_data(covdata, data_paths=['xyzzy'])

    def test_interleaved_erasing_bug716(self):
        # pytest-cov could produce this scenario. #716
        covdata1 = CoverageData()
        covdata2 = CoverageData()
        # this used to create the .coverage database file..
        covdata2.set_context("")
        # then this would erase it all..
        covdata1.erase()
        # then this would try to use tables that no longer exist.
        # "no such table: meta"
        covdata2.add_lines(LINES_1)


class DumpsLoadsTest(DataTestHelpers, CoverageTest):
    """Tests of CoverageData.dumps and loads."""

    run_in_temp_dir = False

    def test_serialization(self):
        covdata1 = CoverageData(no_disk=True)
        covdata1.add_lines(LINES_1)
        covdata1.add_lines(LINES_2)
        serial = covdata1.dumps()

        covdata2 = CoverageData(no_disk=True)
        covdata2.loads(serial)
        self.assert_line_counts(covdata2, SUMMARY_1_2)
        self.assert_measured_files(covdata2, MEASURED_FILES_1_2)

    def test_misfed_serialization(self):
        covdata = CoverageData(no_disk=True)
        bad_data = b'Hello, world!\x07 ' + b'z' * 100
        msg = r"Unrecognized serialization: {} \(head of {} bytes\)".format(
            re.escape(repr(bad_data[:40])),
            len(bad_data),
            )
        with pytest.raises(CoverageException, match=msg):
            covdata.loads(bad_data)
