"""Tests for coverage.data"""

import glob
import json
import os
import os.path

import mock

from coverage.data import CoverageData, CoverageDataFiles
from coverage.files import PathAliases, canonical_filename
from coverage.misc import CoverageException

from tests.coveragetest import CoverageTest, DebugControlString


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
SUMMARY_3_4 = {'x.py': 5, 'y.py': 2, 'z.py': 1}
MEASURED_FILES_3_4 = ['x.py', 'y.py', 'z.py']


class DataTestHelpers(CoverageTest):
    """Test helpers for data tests."""

    def assert_line_counts(self, covdata, line_counts, fullpath=False):
        """Check that the line_counts of `covdata` is `line_counts`."""
        self.assertEqual(covdata.line_counts(fullpath), line_counts)

    def assert_measured_files(self, covdata, measured):
        """Check that `covdata`'s measured files are `measured`."""
        self.assertCountEqual(covdata.measured_files(), measured)


class CoverageDataTest(DataTestHelpers, CoverageTest):
    """Test cases for CoverageData."""

    run_in_temp_dir = False

    def test_empty_data_is_false(self):
        covdata = CoverageData()
        self.assertFalse(covdata)

    def test_line_data_is_true(self):
        covdata = CoverageData()
        covdata.set_lines(LINES_1)
        self.assertTrue(covdata)

    def test_arc_data_is_true(self):
        covdata = CoverageData()
        covdata.set_arcs(ARCS_3)
        self.assertTrue(covdata)

    def test_adding_lines(self):
        covdata = CoverageData()
        covdata.set_lines(LINES_1)
        self.assert_line_counts(covdata, SUMMARY_1)
        self.assert_measured_files(covdata, MEASURED_FILES_1)
        self.assertCountEqual(covdata.lines("a.py"), A_PY_LINES_1)
        self.assertFalse(covdata.has_arcs())

    def test_adding_arcs(self):
        covdata = CoverageData()
        covdata.set_arcs(ARCS_3)
        self.assert_line_counts(covdata, SUMMARY_3)
        self.assert_measured_files(covdata, MEASURED_FILES_3)
        self.assertCountEqual(covdata.lines("x.py"), X_PY_LINES_3)
        self.assertCountEqual(covdata.arcs("x.py"), X_PY_ARCS_3)
        self.assertCountEqual(covdata.lines("y.py"), Y_PY_LINES_3)
        self.assertCountEqual(covdata.arcs("y.py"), Y_PY_ARCS_3)
        self.assertTrue(covdata.has_arcs())

    def test_cant_set_arcs_with_lines(self):
        covdata = CoverageData()
        covdata.set_lines(LINES_1)
        with self.assertRaisesRegex(CoverageException, "Can't add arcs to existing line data"):
            covdata.set_arcs(ARCS_3)

    def test_cant_set_lines_with_arcs(self):
        covdata = CoverageData()
        covdata.set_arcs(ARCS_3)
        with self.assertRaisesRegex(CoverageException, "Can't add lines to existing arc data"):
            covdata.set_lines(LINES_1)

    def test_touch_file_with_lines(self):
        covdata = CoverageData()
        covdata.set_lines(LINES_1)
        covdata.touch_file('zzz.py')
        self.assert_measured_files(covdata, MEASURED_FILES_1 + ['zzz.py'])

    def test_touch_file_with_arcs(self):
        covdata = CoverageData()
        covdata.set_arcs(ARCS_3)
        covdata.touch_file('zzz.py')
        self.assert_measured_files(covdata, MEASURED_FILES_3 + ['zzz.py'])

    def test_no_lines_vs_unmeasured_file(self):
        covdata = CoverageData()
        covdata.set_lines(LINES_1)
        covdata.touch_file('zzz.py')
        self.assertEqual(covdata.lines('zzz.py'), [])
        self.assertIsNone(covdata.lines('no_such_file.py'))

    def test_no_arcs_vs_unmeasured_file(self):
        covdata = CoverageData()
        covdata.set_arcs(ARCS_3)
        covdata.touch_file('zzz.py')
        self.assertEqual(covdata.lines('zzz.py'), [])
        self.assertIsNone(covdata.lines('no_such_file.py'))
        self.assertEqual(covdata.arcs('zzz.py'), [])
        self.assertIsNone(covdata.arcs('no_such_file.py'))

    def test_plugin_name(self):
        covdata = CoverageData()
        covdata.set_lines({
            "p1.foo": dict.fromkeys([1, 2, 3]),
            "p2.html": dict.fromkeys([10, 11, 12]),
            "main.py": dict.fromkeys([20]),
        })
        covdata.set_plugins({"p1.foo": "p1.plugin", "p2.html": "p2.plugin"})
        self.assertEqual(covdata.plugin_name("p1.foo"), "p1.plugin")
        self.assertEqual(covdata.plugin_name("main.py"), "")
        self.assertIsNone(covdata.plugin_name("p3.not_here"))

    def test_cant_plugin_unmeasured_files(self):
        covdata = CoverageData()
        msg = "Can't add plugin data for unmeasured file 'p1.foo'"
        with self.assertRaisesRegex(CoverageException, msg):
            covdata.set_plugins({"p1.foo": "p1.plugin"})

        covdata.set_lines({"p2.html": dict.fromkeys([10, 11, 12])})
        with self.assertRaisesRegex(CoverageException, msg):
            covdata.set_plugins({"p1.foo": "p1.plugin"})

    def test_cant_change_plugin_name(self):
        covdata = CoverageData()
        covdata.set_lines({"p1.foo": dict.fromkeys([1, 2, 3])})
        covdata.set_plugins({"p1.foo": "p1.plugin"})

        msg = "Conflicting plugin name for 'p1.foo': 'p1.plugin' vs 'p1.plugin.foo'"
        with self.assertRaisesRegex(CoverageException, msg):
            covdata.set_plugins({"p1.foo": "p1.plugin.foo"})

    def test_update_lines(self):
        covdata1 = CoverageData()
        covdata1.set_lines(LINES_1)

        covdata2 = CoverageData()
        covdata2.set_lines(LINES_2)

        covdata3 = CoverageData()
        covdata3.update(covdata1)
        covdata3.update(covdata2)

        self.assert_line_counts(covdata3, SUMMARY_1_2)
        self.assert_measured_files(covdata3, MEASURED_FILES_1_2)

    def test_update_arcs(self):
        covdata1 = CoverageData()
        covdata1.set_arcs(ARCS_3)

        covdata2 = CoverageData()
        covdata2.set_arcs(ARCS_4)

        covdata3 = CoverageData()
        covdata3.update(covdata1)
        covdata3.update(covdata2)

        self.assert_line_counts(covdata3, SUMMARY_3_4)
        self.assert_measured_files(covdata3, MEASURED_FILES_3_4)

    def test_update_cant_mix_lines_and_arcs(self):
        covdata1 = CoverageData()
        covdata1.set_lines(LINES_1)

        covdata2 = CoverageData()
        covdata2.set_arcs(ARCS_3)

        with self.assertRaisesRegex(CoverageException, "Can't combine arc data with line data"):
            covdata1.update(covdata2)

        with self.assertRaisesRegex(CoverageException, "Can't combine line data with arc data"):
            covdata2.update(covdata1)

    def test_update_plugins(self):
        covdata1 = CoverageData()
        covdata1.set_lines({
            "p1.html": dict.fromkeys([1, 2, 3, 4]),
            "p2.html": dict.fromkeys([5, 6, 7]),
            "main.py": dict.fromkeys([10, 11, 12]),
        })
        covdata1.set_plugins({
            "p1.html": "html.plugin",
            "p2.html": "html.plugin2",
        })

        covdata2 = CoverageData()
        covdata2.set_lines({
            "p1.html": dict.fromkeys([3, 4, 5, 6]),
            "p2.html": dict.fromkeys([7, 8, 9]),
            "p3.foo": dict.fromkeys([1000, 1001]),
            "main.py": dict.fromkeys([10, 11, 12]),
        })
        covdata2.set_plugins({
            "p1.html": "html.plugin",
            "p2.html": "html.plugin2",
            "p3.foo": "foo_plugin",
        })

        covdata3 = CoverageData()
        covdata3.update(covdata1)
        covdata3.update(covdata2)
        self.assertEqual(covdata3.plugin_name("p1.html"), "html.plugin")
        self.assertEqual(covdata3.plugin_name("p2.html"), "html.plugin2")
        self.assertEqual(covdata3.plugin_name("p3.foo"), "foo_plugin")
        self.assertEqual(covdata3.plugin_name("main.py"), "")

    def test_update_conflicting_plugins(self):
        covdata1 = CoverageData()
        covdata1.set_lines({"p1.html": dict.fromkeys([1, 2, 3])})
        covdata1.set_plugins({"p1.html": "html.plugin"})

        covdata2 = CoverageData()
        covdata2.set_lines({"p1.html": dict.fromkeys([1, 2, 3])})
        covdata2.set_plugins({"p1.html": "html.other_plugin"})

        msg = "Conflicting plugin name for 'p1.html': 'html.plugin' vs 'html.other_plugin'"
        with self.assertRaisesRegex(CoverageException, msg):
            covdata1.update(covdata2)

        msg = "Conflicting plugin name for 'p1.html': 'html.other_plugin' vs 'html.plugin'"
        with self.assertRaisesRegex(CoverageException, msg):
            covdata2.update(covdata1)

    def test_update_plugin_vs_no_plugin(self):
        covdata1 = CoverageData()
        covdata1.set_lines({"p1.html": dict.fromkeys([1, 2, 3])})
        covdata1.set_plugins({"p1.html": "html.plugin"})

        covdata2 = CoverageData()
        covdata2.set_lines({"p1.html": dict.fromkeys([1, 2, 3])})

        msg = "Conflicting plugin name for 'p1.html': 'html.plugin' vs ''"
        with self.assertRaisesRegex(CoverageException, msg):
            covdata1.update(covdata2)

        msg = "Conflicting plugin name for 'p1.html': '' vs 'html.plugin'"
        with self.assertRaisesRegex(CoverageException, msg):
            covdata2.update(covdata1)

    def test_add_to_hash_with_lines(self):
        covdata = CoverageData()
        covdata.set_lines(LINES_1)
        hasher = mock.Mock()
        covdata.add_to_hash("a.py", hasher)
        self.assertEqual(hasher.method_calls, [
            mock.call.update([1, 2]),   # lines
            mock.call.update(""),       # plugin name
        ])

    def test_add_to_hash_with_arcs(self):
        covdata = CoverageData()
        covdata.set_arcs(ARCS_3)
        covdata.set_plugins({"y.py": "hologram_plugin"})
        hasher = mock.Mock()
        covdata.add_to_hash("y.py", hasher)
        self.assertEqual(hasher.method_calls, [
            mock.call.update([(-1, 17), (17, 23), (23, -1)]),   # arcs
            mock.call.update("hologram_plugin"),                # plugin name
        ])


class CoverageDataTestInTempDir(DataTestHelpers, CoverageTest):
    """Tests of CoverageData that need a temp dir to make files."""

    def test_read_write_lines(self):
        covdata1 = CoverageData()
        covdata1.set_lines(LINES_1)
        covdata1.write_file("lines.dat")

        covdata2 = CoverageData()
        covdata2.read_file("lines.dat")
        self.assert_line_counts(covdata2, SUMMARY_1)
        self.assert_measured_files(covdata2, MEASURED_FILES_1)
        self.assertCountEqual(covdata2.lines("a.py"), A_PY_LINES_1)

    def test_read_write_arcs(self):
        covdata1 = CoverageData()
        covdata1.set_arcs(ARCS_3)
        covdata1.write_file("arcs.dat")

        covdata2 = CoverageData()
        covdata2.read_file("arcs.dat")
        self.assert_line_counts(covdata2, SUMMARY_3)
        self.assert_measured_files(covdata2, MEASURED_FILES_3)
        self.assertCountEqual(covdata2.lines("x.py"), X_PY_LINES_3)
        self.assertCountEqual(covdata2.arcs("x.py"), X_PY_ARCS_3)
        self.assertCountEqual(covdata2.lines("y.py"), Y_PY_LINES_3)
        self.assertCountEqual(covdata2.arcs("y.py"), Y_PY_ARCS_3)

    def test_read_errors(self):
        covdata = CoverageData()

        msg = r"Couldn't read data from '{0}': \S+"
        self.make_file("xyzzy.dat", "xyzzy")
        with self.assertRaisesRegex(CoverageException, msg.format("xyzzy.dat")):
            covdata.read_file("xyzzy.dat")

        self.make_file("empty.dat", "")
        with self.assertRaisesRegex(CoverageException, msg.format("empty.dat")):
            covdata.read_file("empty.dat")

        with self.assertRaisesRegex(CoverageException, msg.format("nonexistent.dat")):
            covdata.read_file("nonexistent.dat")

        # and after all that, no data should be in our CoverageData.
        self.assertFalse(covdata)


class CoverageDataFilesTest(DataTestHelpers, CoverageTest):
    """Tests of CoverageDataFiles."""

    no_files_in_temp_dir = True

    def setUp(self):
        super(CoverageDataFilesTest, self).setUp()
        self.data_files = CoverageDataFiles()

    def test_reading_missing(self):
        self.assert_doesnt_exist(".coverage")
        covdata = CoverageData()
        self.data_files.read(covdata)
        self.assert_line_counts(covdata, {})

    def test_writing_and_reading(self):
        covdata1 = CoverageData()
        covdata1.set_lines(LINES_1)
        self.data_files.write(covdata1)

        covdata2 = CoverageData()
        self.data_files.read(covdata2)
        self.assert_line_counts(covdata2, SUMMARY_1)

    def test_debug_output_with_debug_option(self):
        # With debug option dataio, we get debug output about reading and
        # writing files.
        debug = DebugControlString(options=["dataio"])
        covdata1 = CoverageData(debug=debug)
        covdata1.set_lines(LINES_1)
        self.data_files.write(covdata1)

        covdata2 = CoverageData(debug=debug)
        self.data_files.read(covdata2)
        self.assert_line_counts(covdata2, SUMMARY_1)

        self.assertRegex(
            debug.get_output(),
            r"^Writing data to '.*\.coverage'\n"
            r"Reading data from '.*\.coverage'\n$"
        )

    def test_debug_output_without_debug_option(self):
        # With a debug object, but not the dataio option, we don't get debug
        # output.
        debug = DebugControlString(options=[])
        covdata1 = CoverageData(debug=debug)
        covdata1.set_lines(LINES_1)
        self.data_files.write(covdata1)

        covdata2 = CoverageData(debug=debug)
        self.data_files.read(covdata2)
        self.assert_line_counts(covdata2, SUMMARY_1)

        self.assertEqual(debug.get_output(), "")

    def test_explicit_suffix(self):
        self.assert_doesnt_exist(".coverage.SUFFIX")
        covdata = CoverageData()
        covdata.set_lines(LINES_1)
        self.data_files.write(covdata, suffix='SUFFIX')
        self.assert_exists(".coverage.SUFFIX")
        self.assert_doesnt_exist(".coverage")

    def test_true_suffix(self):
        self.assertEqual(glob.glob(".coverage.*"), [])

        # suffix=True will make a randomly named data file.
        covdata1 = CoverageData()
        covdata1.set_lines(LINES_1)
        self.data_files.write(covdata1, suffix=True)
        self.assert_doesnt_exist(".coverage")
        data_files1 = glob.glob(".coverage.*")
        self.assertEqual(len(data_files1), 1)

        # Another suffix=True will choose a different name.
        covdata2 = CoverageData()
        covdata2.set_lines(LINES_1)
        self.data_files.write(covdata2, suffix=True)
        self.assert_doesnt_exist(".coverage")
        data_files2 = glob.glob(".coverage.*")
        self.assertEqual(len(data_files2), 2)

        # In addition to being different, the suffixes have the pid in them.
        self.assertTrue(all(str(os.getpid()) in fn for fn in data_files2))

    def test_combining(self):
        self.assert_doesnt_exist(".coverage.1")
        self.assert_doesnt_exist(".coverage.2")

        covdata1 = CoverageData()
        covdata1.set_lines(LINES_1)
        self.data_files.write(covdata1, suffix='1')
        self.assert_exists(".coverage.1")
        self.assert_doesnt_exist(".coverage.2")

        covdata2 = CoverageData()
        covdata2.set_lines(LINES_2)
        self.data_files.write(covdata2, suffix='2')
        self.assert_exists(".coverage.2")

        covdata3 = CoverageData()
        self.data_files.combine_parallel_data(covdata3)
        self.assert_line_counts(covdata3, SUMMARY_1_2)
        self.assert_measured_files(covdata3, MEASURED_FILES_1_2)
        self.assert_doesnt_exist(".coverage.1")
        self.assert_doesnt_exist(".coverage.2")

    def test_erasing(self):
        covdata1 = CoverageData()
        covdata1.set_lines(LINES_1)
        self.data_files.write(covdata1)

        covdata1.erase()
        self.assert_line_counts(covdata1, {})

        self.data_files.erase()
        covdata2 = CoverageData()
        self.data_files.read(covdata2)
        self.assert_line_counts(covdata2, {})

    def test_file_format(self):
        # Write with CoverageData, then read the JSON explicitly.
        covdata = CoverageData()
        covdata.set_lines(LINES_1)
        self.data_files.write(covdata)

        with open(".coverage", 'r') as fdata:
            data = json.load(fdata)

        lines = data['lines']
        self.assertCountEqual(lines.keys(), MEASURED_FILES_1)
        self.assertCountEqual(lines['a.py'], A_PY_LINES_1)
        self.assertCountEqual(lines['b.py'], B_PY_LINES_1)
        # If not measuring branches, there's no arcs entry.
        self.assertNotIn('arcs', data)
        # If no plugins were involved, there's no plugins entry.
        self.assertNotIn('plugins', data)

    def test_file_format_with_arcs(self):
        # Write with CoverageData, then read the JSON explicitly.
        covdata = CoverageData()
        covdata.set_arcs(ARCS_3)
        self.data_files.write(covdata)

        with open(".coverage", 'r') as fdata:
            data = json.load(fdata)

        self.assertNotIn('lines', data)
        arcs = data['arcs']
        self.assertCountEqual(arcs.keys(), MEASURED_FILES_3)
        self.assertCountEqual(arcs['x.py'], map(list, X_PY_ARCS_3))
        self.assertCountEqual(arcs['y.py'], map(list, Y_PY_ARCS_3))
        # If no plugins were involved, there's no plugins entry.
        self.assertNotIn('plugins', data)

    def test_writing_to_other_file(self):
        data_files = CoverageDataFiles(".otherfile")
        covdata = CoverageData()
        covdata.set_lines(LINES_1)
        data_files.write(covdata)
        self.assert_doesnt_exist(".coverage")
        self.assert_exists(".otherfile")

        data_files.write(covdata, suffix="extra")
        self.assert_exists(".otherfile.extra")
        self.assert_doesnt_exist(".coverage")

    def test_combining_with_aliases(self):
        covdata1 = CoverageData()
        covdata1.set_lines({
            '/home/ned/proj/src/a.py': {1: None, 2: None},
            '/home/ned/proj/src/sub/b.py': {3: None},
            '/home/ned/proj/src/template.html': {10: None},
        })
        covdata1.set_plugins({
            '/home/ned/proj/src/template.html': 'html.plugin',
        })
        self.data_files.write(covdata1, suffix='1')

        covdata2 = CoverageData()
        covdata2.set_lines({
            r'c:\ned\test\a.py': {4: None, 5: None},
            r'c:\ned\test\sub\b.py': {3: None, 6: None},
        })
        self.data_files.write(covdata2, suffix='2')

        covdata3 = CoverageData()
        aliases = PathAliases()
        aliases.add("/home/ned/proj/src/", "./")
        aliases.add(r"c:\ned\test", "./")
        self.data_files.combine_parallel_data(covdata3, aliases=aliases)

        apy = canonical_filename('./a.py')
        sub_bpy = canonical_filename('./sub/b.py')
        template_html = canonical_filename('./template.html')

        self.assert_line_counts(covdata3, {apy: 4, sub_bpy: 2, template_html: 1}, fullpath=True)
        self.assert_measured_files(covdata3, [apy, sub_bpy, template_html])
        self.assertEqual(covdata3.plugin_name(template_html), 'html.plugin')

    def test_combining_from_different_directories(self):
        covdata1 = CoverageData()
        covdata1.set_lines(LINES_1)
        os.makedirs('cov1')
        covdata1.write_file('cov1/.coverage.1')

        covdata2 = CoverageData()
        covdata2.set_lines(LINES_2)
        os.makedirs('cov2')
        covdata2.write_file('cov2/.coverage.2')

        covdata3 = CoverageData()
        self.data_files.combine_parallel_data(covdata3, data_dirs=['cov1/', 'cov2/'])

        self.assert_line_counts(covdata3, SUMMARY_1_2)
        self.assert_measured_files(covdata3, MEASURED_FILES_1_2)
        self.assert_doesnt_exist("cov1/.coverage.1")
        self.assert_doesnt_exist("cov2/.coverage.2")
