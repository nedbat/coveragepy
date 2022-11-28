# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Tests for coverage.py's API."""

import fnmatch
import glob
import io
import os
import os.path
import re
import shutil
import sys
import textwrap

import pytest

import coverage
from coverage import env
from coverage.data import line_counts
from coverage.exceptions import CoverageException, DataError, NoDataError, NoSource
from coverage.files import abs_file, relative_filename
from coverage.misc import import_local_file

from tests.coveragetest import CoverageTest, TESTS_DIR, UsingModulesMixin
from tests.goldtest import contains, doesnt_contain
from tests.helpers import arcz_to_arcs, assert_count_equal, assert_coverage_warnings
from tests.helpers import change_dir, nice_file, os_sep

BAD_SQLITE_REGEX = r"file( is encrypted or)? is not a database"

class ApiTest(CoverageTest):
    """Api-oriented tests for coverage.py."""

    def clean_files(self, files, pats):
        """Remove names matching `pats` from `files`, a list of file names."""
        good = []
        for f in files:
            for pat in pats:
                if fnmatch.fnmatch(f, pat):
                    break
            else:
                good.append(f)
        return good

    def assertFiles(self, files):
        """Assert that the files here are `files`, ignoring the usual junk."""
        here = os.listdir(".")
        here = self.clean_files(here, ["*.pyc", "__pycache__", "*$py.class"])
        assert_count_equal(here, files)

    def test_unexecuted_file(self):
        cov = coverage.Coverage()

        self.make_file("mycode.py", """\
            a = 1
            b = 2
            if b == 3:
                c = 4
            d = 5
            """)

        self.make_file("not_run.py", """\
            fooey = 17
            """)

        # Import the Python file, executing it.
        self.start_import_stop(cov, "mycode")

        _, statements, missing, _ = cov.analysis("not_run.py")
        assert statements == [1]
        assert missing == [1]

    def test_filenames(self):
        self.make_file("mymain.py", """\
            import mymod
            a = 1
            """)

        self.make_file("mymod.py", """\
            fooey = 17
            """)

        # Import the Python file, executing it.
        cov = coverage.Coverage()
        self.start_import_stop(cov, "mymain")

        filename, _, _, _ = cov.analysis("mymain.py")
        assert os.path.basename(filename) == "mymain.py"
        filename, _, _, _ = cov.analysis("mymod.py")
        assert os.path.basename(filename) == "mymod.py"

        filename, _, _, _ = cov.analysis(sys.modules["mymain"])
        assert os.path.basename(filename) == "mymain.py"
        filename, _, _, _ = cov.analysis(sys.modules["mymod"])
        assert os.path.basename(filename) == "mymod.py"

        # Import the Python file, executing it again, once it's been compiled
        # already.
        cov = coverage.Coverage()
        self.start_import_stop(cov, "mymain")

        filename, _, _, _ = cov.analysis("mymain.py")
        assert os.path.basename(filename) == "mymain.py"
        filename, _, _, _ = cov.analysis("mymod.py")
        assert os.path.basename(filename) == "mymod.py"

        filename, _, _, _ = cov.analysis(sys.modules["mymain"])
        assert os.path.basename(filename) == "mymain.py"
        filename, _, _, _ = cov.analysis(sys.modules["mymod"])
        assert os.path.basename(filename) == "mymod.py"

    def test_ignore_stdlib(self):
        self.make_file("mymain.py", """\
            import colorsys
            a = 1
            hls = colorsys.rgb_to_hls(1.0, 0.5, 0.0)
            """)

        # Measure without the stdlib.
        cov1 = coverage.Coverage()
        assert cov1.config.cover_pylib is False
        self.start_import_stop(cov1, "mymain")

        # some statements were marked executed in mymain.py
        _, statements, missing, _ = cov1.analysis("mymain.py")
        assert statements != missing
        # but none were in colorsys.py
        _, statements, missing, _ = cov1.analysis("colorsys.py")
        assert statements == missing

        # Measure with the stdlib.
        cov2 = coverage.Coverage(cover_pylib=True)
        self.start_import_stop(cov2, "mymain")

        # some statements were marked executed in mymain.py
        _, statements, missing, _ = cov2.analysis("mymain.py")
        assert statements != missing
        # and some were marked executed in colorsys.py
        _, statements, missing, _ = cov2.analysis("colorsys.py")
        assert statements != missing

    def test_include_can_measure_stdlib(self):
        self.make_file("mymain.py", """\
            import colorsys, random
            a = 1
            r, g, b = [random.random() for _ in range(3)]
            hls = colorsys.rgb_to_hls(r, g, b)
            """)

        # Measure without the stdlib, but include colorsys.
        cov1 = coverage.Coverage(cover_pylib=False, include=["*/colorsys.py"])
        self.start_import_stop(cov1, "mymain")

        # some statements were marked executed in colorsys.py
        _, statements, missing, _ = cov1.analysis("colorsys.py")
        assert statements != missing
        # but none were in random.py
        _, statements, missing, _ = cov1.analysis("random.py")
        assert statements == missing

    def test_exclude_list(self):
        cov = coverage.Coverage()
        cov.clear_exclude()
        assert cov.get_exclude_list() == []
        cov.exclude("foo")
        assert cov.get_exclude_list() == ["foo"]
        cov.exclude("bar")
        assert cov.get_exclude_list() == ["foo", "bar"]
        assert cov._exclude_regex('exclude') == "(?:foo)|(?:bar)"
        cov.clear_exclude()
        assert cov.get_exclude_list() == []

    def test_exclude_partial_list(self):
        cov = coverage.Coverage()
        cov.clear_exclude(which='partial')
        assert cov.get_exclude_list(which='partial') == []
        cov.exclude("foo", which='partial')
        assert cov.get_exclude_list(which='partial') == ["foo"]
        cov.exclude("bar", which='partial')
        assert cov.get_exclude_list(which='partial') == ["foo", "bar"]
        assert cov._exclude_regex(which='partial') == "(?:foo)|(?:bar)"
        cov.clear_exclude(which='partial')
        assert cov.get_exclude_list(which='partial') == []

    def test_exclude_and_partial_are_separate_lists(self):
        cov = coverage.Coverage()
        cov.clear_exclude(which='partial')
        cov.clear_exclude(which='exclude')
        cov.exclude("foo", which='partial')
        assert cov.get_exclude_list(which='partial') == ['foo']
        assert cov.get_exclude_list(which='exclude') == []
        cov.exclude("bar", which='exclude')
        assert cov.get_exclude_list(which='partial') == ['foo']
        assert cov.get_exclude_list(which='exclude') == ['bar']
        cov.exclude("p2", which='partial')
        cov.exclude("e2", which='exclude')
        assert cov.get_exclude_list(which='partial') == ['foo', 'p2']
        assert cov.get_exclude_list(which='exclude') == ['bar', 'e2']
        cov.clear_exclude(which='partial')
        assert cov.get_exclude_list(which='partial') == []
        assert cov.get_exclude_list(which='exclude') == ['bar', 'e2']
        cov.clear_exclude(which='exclude')
        assert cov.get_exclude_list(which='partial') == []
        assert cov.get_exclude_list(which='exclude') == []

    def test_datafile_default(self):
        # Default data file behavior: it's .coverage
        self.make_file("datatest1.py", """\
            fooey = 17
            """)

        self.assertFiles(["datatest1.py"])
        cov = coverage.Coverage()
        self.start_import_stop(cov, "datatest1")
        cov.save()
        self.assertFiles(["datatest1.py", ".coverage"])

    def test_datafile_specified(self):
        # You can specify the data file name.
        self.make_file("datatest2.py", """\
            fooey = 17
            """)

        self.assertFiles(["datatest2.py"])
        cov = coverage.Coverage(data_file="cov.data")
        self.start_import_stop(cov, "datatest2")
        cov.save()
        self.assertFiles(["datatest2.py", "cov.data"])

    def test_datafile_and_suffix_specified(self):
        # You can specify the data file name and suffix.
        self.make_file("datatest3.py", """\
            fooey = 17
            """)

        self.assertFiles(["datatest3.py"])
        cov = coverage.Coverage(data_file="cov.data", data_suffix="14")
        self.start_import_stop(cov, "datatest3")
        cov.save()
        self.assertFiles(["datatest3.py", "cov.data.14"])

    def test_datafile_from_rcfile(self):
        # You can specify the data file name in the .coveragerc file
        self.make_file("datatest4.py", """\
            fooey = 17
            """)
        self.make_file(".coveragerc", """\
            [run]
            data_file = mydata.dat
            """)

        self.assertFiles(["datatest4.py", ".coveragerc"])
        cov = coverage.Coverage()
        self.start_import_stop(cov, "datatest4")
        cov.save()
        self.assertFiles(["datatest4.py", ".coveragerc", "mydata.dat"])

    def test_deep_datafile(self):
        self.make_file("datatest5.py", "fooey = 17")
        self.assertFiles(["datatest5.py"])
        cov = coverage.Coverage(data_file="deep/sub/cov.data")
        self.start_import_stop(cov, "datatest5")
        cov.save()
        self.assertFiles(["datatest5.py", "deep"])
        self.assert_exists("deep/sub/cov.data")

    def test_datafile_none(self):
        cov = coverage.Coverage(data_file=None)

        def f1():       # pragma: nested
            a = 1       # pylint: disable=unused-variable

        one_line_number = f1.__code__.co_firstlineno + 1
        lines = []

        def run_one_function(f):
            cov.erase()
            cov.start()
            f()
            cov.stop()

            fs = cov.get_data().measured_files()
            lines.append(cov.get_data().lines(list(fs)[0]))

        run_one_function(f1)
        run_one_function(f1)
        run_one_function(f1)
        assert lines == [[one_line_number]] * 3
        self.assert_doesnt_exist(".coverage")
        assert os.listdir(".") == []

    def test_empty_reporting(self):
        # empty summary reports raise exception, just like the xml report
        cov = coverage.Coverage()
        cov.erase()
        with pytest.raises(NoDataError, match="No data to report."):
            cov.report()

    def test_completely_zero_reporting(self):
        # https://github.com/nedbat/coveragepy/issues/884
        # If nothing was measured, the file-touching didn't happen properly.
        self.make_file("foo/bar.py", "print('Never run')")
        self.make_file("test.py", "assert True")
        with pytest.warns(Warning) as warns:
            cov = coverage.Coverage(source=["foo"])
            self.start_import_stop(cov, "test")
            cov.report()
        assert_coverage_warnings(warns, "No data was collected. (no-data-collected)")
        # Name         Stmts   Miss  Cover
        # --------------------------------
        # foo/bar.py       1      1     0%
        # --------------------------------
        # TOTAL            1      1     0%

        last = self.last_line_squeezed(self.stdout())
        assert "TOTAL 1 1 0%" == last

    def test_cov4_data_file(self):
        cov4_data = (
            "!coverage.py: This is a private format, don't read it directly!" +
            '{"lines":{"/private/tmp/foo.py":[1,5,2,3]}}'
        )
        self.make_file(".coverage", cov4_data)
        cov = coverage.Coverage()
        with pytest.raises(DataError, match="Looks like a coverage 4.x data file"):
            cov.load()
        cov.erase()

    def make_code1_code2(self):
        """Create the code1.py and code2.py files."""
        self.make_file("code1.py", """\
            code1 = 1
            """)
        self.make_file("code2.py", """\
            code2 = 1
            code2 = 2
            """)

    def check_code1_code2(self, cov):
        """Check the analysis is correct for code1.py and code2.py."""
        _, statements, missing, _ = cov.analysis("code1.py")
        assert statements == [1]
        assert missing == []
        _, statements, missing, _ = cov.analysis("code2.py")
        assert statements == [1, 2]
        assert missing == []

    def test_start_stop_start_stop(self):
        self.make_code1_code2()
        cov = coverage.Coverage()
        self.start_import_stop(cov, "code1")
        cov.save()
        self.start_import_stop(cov, "code2")
        self.check_code1_code2(cov)

    def test_start_save_stop(self):
        self.make_code1_code2()
        cov = coverage.Coverage()
        cov.start()
        import_local_file("code1")                                     # pragma: nested
        cov.save()                                                     # pragma: nested
        import_local_file("code2")                                     # pragma: nested
        cov.stop()                                                     # pragma: nested
        self.check_code1_code2(cov)

    def test_start_save_nostop(self):
        self.make_code1_code2()
        cov = coverage.Coverage()
        cov.start()
        import_local_file("code1")                                     # pragma: nested
        cov.save()                                                     # pragma: nested
        import_local_file("code2")                                     # pragma: nested
        self.check_code1_code2(cov)                                    # pragma: nested
        # Then stop it, or the test suite gets out of whack.
        cov.stop()                                                     # pragma: nested

    def test_two_getdata_only_warn_once(self):
        self.make_code1_code2()
        cov = coverage.Coverage(source=["."], omit=["code1.py"])
        cov.start()
        import_local_file("code1")                                     # pragma: nested
        cov.stop()                                                     # pragma: nested
        # We didn't collect any data, so we should get a warning.
        with self.assert_warnings(cov, ["No data was collected"]):
            cov.get_data()
        # But calling get_data a second time with no intervening activity
        # won't make another warning.
        with self.assert_warnings(cov, []):
            cov.get_data()

    def test_two_getdata_warn_twice(self):
        self.make_code1_code2()
        cov = coverage.Coverage(source=["."], omit=["code1.py", "code2.py"])
        cov.start()
        import_local_file("code1")                                     # pragma: nested
        # We didn't collect any data, so we should get a warning.
        with self.assert_warnings(cov, ["No data was collected"]):     # pragma: nested
            cov.save()                                                 # pragma: nested
        import_local_file("code2")                                     # pragma: nested
        # Calling get_data a second time after tracing some more will warn again.
        with self.assert_warnings(cov, ["No data was collected"]):     # pragma: nested
            cov.get_data()                                             # pragma: nested
        # Then stop it, or the test suite gets out of whack.
        cov.stop()                                                     # pragma: nested

    def make_good_data_files(self):
        """Make some good data files."""
        self.make_code1_code2()
        cov = coverage.Coverage(data_suffix=True)
        self.start_import_stop(cov, "code1")
        cov.save()

        cov = coverage.Coverage(data_suffix=True)
        self.start_import_stop(cov, "code2")
        cov.save()
        self.assert_file_count(".coverage.*", 2)

    def test_combining_corrupt_data(self):
        # If you combine a corrupt data file, then you will get a warning,
        # and the file will remain.
        self.make_good_data_files()
        self.make_file(".coverage.foo", """La la la, this isn't coverage data!""")
        cov = coverage.Coverage()
        warning_regex = (
            r"Couldn't use data file '.*\.coverage\.foo': " + BAD_SQLITE_REGEX
        )
        with self.assert_warnings(cov, [warning_regex]):
            cov.combine()

        # We got the results from code1 and code2 properly.
        self.check_code1_code2(cov)

        # The bad file still exists, but it's the only parallel data file left.
        self.assert_exists(".coverage.foo")
        self.assert_file_count(".coverage.*", 1)

    def test_combining_twice(self):
        self.make_good_data_files()
        cov1 = coverage.Coverage()
        cov1.combine()
        assert self.stdout() == ""
        cov1.save()
        self.check_code1_code2(cov1)
        self.assert_file_count(".coverage.*", 0)
        self.assert_exists(".coverage")

        cov2 = coverage.Coverage()
        with pytest.raises(NoDataError, match=r"No data to combine"):
            cov2.combine(strict=True, keep=False)

        cov3 = coverage.Coverage()
        cov3.combine()
        assert self.stdout() == ""
        # Now the data is empty!
        _, statements, missing, _ = cov3.analysis("code1.py")
        assert statements == [1]
        assert missing == [1]
        _, statements, missing, _ = cov3.analysis("code2.py")
        assert statements == [1, 2]
        assert missing == [1, 2]

    def test_combining_with_a_used_coverage(self):
        # Can you use a coverage object to run one shard of a parallel suite,
        # and then also combine the data?
        self.make_code1_code2()
        cov = coverage.Coverage(data_suffix=True)
        self.start_import_stop(cov, "code1")
        cov.save()

        cov = coverage.Coverage(data_suffix=True)
        self.start_import_stop(cov, "code2")
        cov.save()

        cov.combine()
        assert self.stdout() == ""
        self.check_code1_code2(cov)

    def test_ordered_combine(self):
        # https://github.com/nedbat/coveragepy/issues/649
        # The order of the [paths] setting used to matter. Now the
        # resulting path must exist, so the order doesn't matter.
        def make_files():
            self.make_file("plugins/p1.py", "")
            self.make_file("girder/g1.py", "")
            self.make_data_file(
                basename=".coverage.1",
                lines={
                    abs_file('ci/girder/g1.py'): range(10),
                    abs_file('ci/girder/plugins/p1.py'): range(10),
                },
            )

        def get_combined_filenames():
            cov = coverage.Coverage()
            cov.combine()
            assert self.stdout() == ""
            cov.save()
            data = cov.get_data()
            filenames = {relative_filename(f).replace("\\", "/") for f in data.measured_files()}
            return filenames

        # Case 1: get the order right.
        make_files()
        self.make_file(".coveragerc", """\
            [paths]
            plugins =
                plugins/
                ci/girder/plugins/
            girder =
                girder/
                ci/girder/
            """)
        assert get_combined_filenames() == {'girder/g1.py', 'plugins/p1.py'}

        # Case 2: get the order "wrong".
        make_files()
        self.make_file(".coveragerc", """\
            [paths]
            girder =
                girder/
                ci/girder/
            plugins =
                plugins/
                ci/girder/plugins/
            """)
        assert get_combined_filenames() == {'girder/g1.py', 'plugins/p1.py'}

    def test_warnings(self):
        self.make_file("hello.py", """\
            import sys, os
            print("Hello")
            """)
        with pytest.warns(Warning) as warns:
            cov = coverage.Coverage(source=["sys", "xyzzy", "quux"])
            self.start_import_stop(cov, "hello")
            cov.get_data()

        assert "Hello\n" == self.stdout()
        assert_coverage_warnings(
            warns,
            "Module sys has no Python source. (module-not-python)",
            "Module xyzzy was never imported. (module-not-imported)",
            "Module quux was never imported. (module-not-imported)",
            "No data was collected. (no-data-collected)",
        )

    def test_warnings_suppressed(self):
        self.make_file("hello.py", """\
            import sys, os
            print("Hello")
            """)
        self.make_file(".coveragerc", """\
            [run]
            disable_warnings = no-data-collected, module-not-imported
            """)
        with pytest.warns(Warning) as warns:
            cov = coverage.Coverage(source=["sys", "xyzzy", "quux"])
            self.start_import_stop(cov, "hello")
            cov.get_data()

        assert "Hello\n" == self.stdout()
        assert_coverage_warnings(warns, "Module sys has no Python source. (module-not-python)")
        # No "module-not-imported" in warns
        # No "no-data-collected" in warns

    def test_warn_once(self):
        with pytest.warns(Warning) as warns:
            cov = coverage.Coverage()
            cov.load()
            cov._warn("Warning, warning 1!", slug="bot", once=True)
            cov._warn("Warning, warning 2!", slug="bot", once=True)

        assert_coverage_warnings(warns, "Warning, warning 1! (bot)")
        # No "Warning, warning 2!" in warns

    def test_source_and_include_dont_conflict(self):
        # A bad fix made this case fail: https://github.com/nedbat/coveragepy/issues/541
        self.make_file("a.py", "import b\na = 1")
        self.make_file("b.py", "b = 1")
        self.make_file(".coveragerc", """\
            [run]
            source = .
            """)

        # Just like: coverage run a.py
        cov = coverage.Coverage()
        self.start_import_stop(cov, "a")
        cov.save()

        # Run the equivalent of: coverage report --include=b.py
        cov = coverage.Coverage(include=["b.py"])
        cov.load()
        # There should be no exception. At one point, report() threw:
        # CoverageException: --include and --source are mutually exclusive
        cov.report()
        expected = textwrap.dedent("""\
            Name    Stmts   Miss  Cover
            ---------------------------
            b.py        1      0   100%
            ---------------------------
            TOTAL       1      0   100%
            """)
        assert expected == self.stdout()

    def make_test_files(self):
        """Create a simple file representing a method with two tests.

        Returns absolute path to the file.
        """
        self.make_file("testsuite.py", """\
            def timestwo(x):
                return x*2

            def test_multiply_zero():
                assert timestwo(0) == 0

            def test_multiply_six():
                assert timestwo(6) == 12
            """)

    def test_switch_context_testrunner(self):
        # This test simulates a coverage-aware test runner,
        # measuring labeled coverage via public API
        self.make_test_files()

        # Test runner starts
        cov = coverage.Coverage()
        cov.start()

        if "pragma: nested":
            # Imports the test suite
            suite = import_local_file("testsuite")

            # Measures test case 1
            cov.switch_context('multiply_zero')
            suite.test_multiply_zero()

            # Measures test case 2
            cov.switch_context('multiply_six')
            suite.test_multiply_six()

            # Runner finishes
            cov.save()
            cov.stop()

        # Labeled data is collected
        data = cov.get_data()
        assert ['', 'multiply_six', 'multiply_zero'] == sorted(data.measured_contexts())

        filenames = self.get_measured_filenames(data)
        suite_filename = filenames['testsuite.py']

        data.set_query_context("multiply_six")
        assert [2, 8] == sorted(data.lines(suite_filename))
        data.set_query_context("multiply_zero")
        assert [2, 5] == sorted(data.lines(suite_filename))

    def test_switch_context_with_static(self):
        # This test simulates a coverage-aware test runner,
        # measuring labeled coverage via public API,
        # with static label prefix.
        self.make_test_files()

        # Test runner starts
        cov = coverage.Coverage(context="mysuite")
        cov.start()

        if "pragma: nested":
            # Imports the test suite
            suite = import_local_file("testsuite")

            # Measures test case 1
            cov.switch_context('multiply_zero')
            suite.test_multiply_zero()

            # Measures test case 2
            cov.switch_context('multiply_six')
            suite.test_multiply_six()

            # Runner finishes
            cov.save()
            cov.stop()

        # Labeled data is collected
        data = cov.get_data()
        expected = ['mysuite', 'mysuite|multiply_six', 'mysuite|multiply_zero']
        assert expected == sorted(data.measured_contexts())

        filenames = self.get_measured_filenames(data)
        suite_filename = filenames['testsuite.py']

        data.set_query_context("mysuite|multiply_six")
        assert [2, 8] == sorted(data.lines(suite_filename))
        data.set_query_context("mysuite|multiply_zero")
        assert [2, 5] == sorted(data.lines(suite_filename))

    def test_dynamic_context_conflict(self):
        cov = coverage.Coverage(source=["."])
        cov.set_option("run:dynamic_context", "test_function")
        cov.start()
        with pytest.warns(Warning) as warns:
            # Switch twice, but only get one warning.
            cov.switch_context("test1")                                 # pragma: nested
            cov.switch_context("test2")                                 # pragma: nested
        cov.stop()                                                      # pragma: nested
        assert_coverage_warnings(warns, "Conflicting dynamic contexts (dynamic-conflict)")

    def test_switch_context_unstarted(self):
        # Coverage must be started to switch context
        msg = "Cannot switch context, coverage is not started"
        cov = coverage.Coverage()
        with pytest.raises(CoverageException, match=msg):
            cov.switch_context("test1")

        cov.start()
        cov.switch_context("test2")                                     # pragma: nested

        cov.stop()                                                      # pragma: nested
        with pytest.raises(CoverageException, match=msg):
            cov.switch_context("test3")

    def test_config_crash(self):
        # The internal '[run] _crash' setting can be used to artificially raise
        # exceptions from inside Coverage.
        cov = coverage.Coverage()
        cov.set_option("run:_crash", "test_config_crash")
        with pytest.raises(Exception, match="Crashing because called by test_config_crash"):
            cov.start()

    def test_config_crash_no_crash(self):
        # '[run] _crash' really checks the call stack.
        cov = coverage.Coverage()
        cov.set_option("run:_crash", "not_my_caller")
        cov.start()
        cov.stop()

    def test_run_debug_sys(self):
        # https://github.com/nedbat/coveragepy/issues/907
        cov = coverage.Coverage()
        cov.start()
        d = dict(cov.sys_info())        # pragma: nested
        cov.stop()                      # pragma: nested
        assert d['data_file'].endswith(".coverage")


class CurrentInstanceTest(CoverageTest):
    """Tests of Coverage.current()."""

    run_in_temp_dir = False

    def assert_current_is_none(self, current):
        """Assert that a current we expect to be None is correct."""
        # During meta-coverage, the None answers will be wrong because the
        # overall coverage measurement will still be on the current-stack.
        # Since we know they will be wrong, and we have non-meta test runs
        # also, don't assert them.
        if not env.METACOV:
            assert current is None

    def test_current(self):
        cur0 = coverage.Coverage.current()
        self.assert_current_is_none(cur0)
        # Making an instance doesn't make it current.
        cov = coverage.Coverage()
        cur1 = coverage.Coverage.current()
        self.assert_current_is_none(cur1)
        assert cur0 is cur1
        # Starting the instance makes it current.
        cov.start()
        if "# pragma: nested":
            cur2 = coverage.Coverage.current()
            assert cur2 is cov
            # Stopping the instance makes current None again.
            cov.stop()

        cur3 = coverage.Coverage.current()
        self.assert_current_is_none(cur3)
        assert cur0 is cur3


class NamespaceModuleTest(UsingModulesMixin, CoverageTest):
    """Test PEP-420 namespace modules."""

    def test_explicit_namespace_module(self):
        self.make_file("main.py", "import namespace_420\n")

        cov = coverage.Coverage()
        self.start_import_stop(cov, "main")

        with pytest.raises(CoverageException, match=r"Module .* has no file"):
            cov.analysis(sys.modules['namespace_420'])

    def test_bug_572(self):
        self.make_file("main.py", "import namespace_420\n")

        # Use source=namespace_420 to trigger the check that used to fail,
        # and use source=main so that something is measured.
        cov = coverage.Coverage(source=["namespace_420", "main"])
        with self.assert_warnings(cov, []):
            self.start_import_stop(cov, "main")
            cov.report()


class IncludeOmitTestsMixin(UsingModulesMixin, CoverageTest):
    """Test methods for coverage methods taking include and omit."""

    def filenames_in(self, summary, filenames):
        """Assert the `filenames` are in the keys of `summary`."""
        for filename in filenames.split():
            assert filename in summary

    def filenames_not_in(self, summary, filenames):
        """Assert the `filenames` are not in the keys of `summary`."""
        for filename in filenames.split():
            assert filename not in summary

    def test_nothing_specified(self):
        result = self.coverage_usepkgs()
        self.filenames_in(result, "p1a p1b p2a p2b othera otherb osa osb")
        self.filenames_not_in(result, "p1c")
        # Because there was no source= specified, we don't search for
        # un-executed files.

    def test_include(self):
        result = self.coverage_usepkgs(include=["*/p1a.py"])
        self.filenames_in(result, "p1a")
        self.filenames_not_in(result, "p1b p1c p2a p2b othera otherb osa osb")

    def test_include_2(self):
        result = self.coverage_usepkgs(include=["*a.py"])
        self.filenames_in(result, "p1a p2a othera osa")
        self.filenames_not_in(result, "p1b p1c p2b otherb osb")

    def test_include_as_string(self):
        result = self.coverage_usepkgs(include="*a.py")
        self.filenames_in(result, "p1a p2a othera osa")
        self.filenames_not_in(result, "p1b p1c p2b otherb osb")

    def test_omit(self):
        result = self.coverage_usepkgs(omit=["*/p1a.py"])
        self.filenames_in(result, "p1b p2a p2b")
        self.filenames_not_in(result, "p1a p1c")

    def test_omit_2(self):
        result = self.coverage_usepkgs(omit=["*a.py"])
        self.filenames_in(result, "p1b p2b otherb osb")
        self.filenames_not_in(result, "p1a p1c p2a othera osa")

    def test_omit_as_string(self):
        result = self.coverage_usepkgs(omit="*a.py")
        self.filenames_in(result, "p1b p2b otherb osb")
        self.filenames_not_in(result, "p1a p1c p2a othera osa")

    def test_omit_and_include(self):
        result = self.coverage_usepkgs(include=["*/p1*"], omit=["*/p1a.py"])
        self.filenames_in(result, "p1b")
        self.filenames_not_in(result, "p1a p1c p2a p2b")


class SourceIncludeOmitTest(IncludeOmitTestsMixin, CoverageTest):
    """Test using `source`, `include`, and `omit` when measuring code."""

    def setUp(self):
        super().setUp()

        # These tests use the TESTS_DIR/modules files, but they cd into it. To
        # keep tests from cross-contaminating, we make a copy of the files.
        # Since we need to import from there, we also add it to the beginning
        # of sys.path.

        shutil.copytree(
            nice_file(TESTS_DIR, "modules"),
            "tests_dir_modules",
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        sys.path.insert(0, abs_file("tests_dir_modules"))

    def coverage_usepkgs(self, **kwargs):
        """Run coverage on usepkgs and return the line summary.

        Arguments are passed to the `coverage.Coverage` constructor.

        """
        cov = coverage.Coverage(**kwargs)
        cov.start()
        import usepkgs  # pragma: nested   # pylint: disable=import-error, unused-import
        cov.stop()      # pragma: nested
        with self.assert_warnings(cov, []):
            data = cov.get_data()
        summary = line_counts(data)
        for k, v in list(summary.items()):
            assert k.endswith(".py")
            summary[k[:-3]] = v
        return summary

    def test_source_include_exclusive(self):
        cov = coverage.Coverage(source=["pkg1"], include=["pkg2"])
        with self.assert_warnings(cov, ["--include is ignored because --source is set"]):
            cov.start()
        cov.stop()      # pragma: nested

    def test_source_package_as_package(self):
        assert not os.path.isdir("pkg1")
        lines = self.coverage_usepkgs(source=["pkg1"])
        self.filenames_in(lines, "p1a p1b")
        self.filenames_not_in(lines, "p2a p2b othera otherb osa osb")
        # Because source= was specified, we do search for un-executed files.
        assert lines['p1c'] == 0

    def test_source_package_as_dir(self):
        os.chdir("tests_dir_modules")
        assert os.path.isdir("pkg1")
        lines = self.coverage_usepkgs(source=["pkg1"])
        self.filenames_in(lines, "p1a p1b")
        self.filenames_not_in(lines, "p2a p2b othera otherb osa osb")
        # Because source= was specified, we do search for un-executed files.
        assert lines['p1c'] == 0

    def test_source_package_dotted_sub(self):
        lines = self.coverage_usepkgs(source=["pkg1.sub"])
        self.filenames_not_in(lines, "p2a p2b othera otherb osa osb")
        # Because source= was specified, we do search for un-executed files.
        assert lines['runmod3'] == 0

    def test_source_package_dotted_p1b(self):
        lines = self.coverage_usepkgs(source=["pkg1.p1b"])
        self.filenames_in(lines, "p1b")
        self.filenames_not_in(lines, "p1a p1c p2a p2b othera otherb osa osb")

    def test_source_package_part_omitted(self):
        # https://github.com/nedbat/coveragepy/issues/218
        # Used to be if you omitted something executed and inside the source,
        # then after it was executed but not recorded, it would be found in
        # the search for un-executed files, and given a score of 0%.

        # The omit arg is by path, so need to be in the modules directory.
        os.chdir("tests_dir_modules")
        lines = self.coverage_usepkgs(source=["pkg1"], omit=["pkg1/p1b.py"])
        self.filenames_in(lines, "p1a")
        self.filenames_not_in(lines, "p1b")
        assert lines['p1c'] == 0

    def test_source_package_as_package_part_omitted(self):
        # https://github.com/nedbat/coveragepy/issues/638
        lines = self.coverage_usepkgs(source=["pkg1"], omit=["*/p1b.py"])
        self.filenames_in(lines, "p1a")
        self.filenames_not_in(lines, "p1b")
        assert lines['p1c'] == 0

    def test_ambiguous_source_package_as_dir(self):
        # pkg1 is a directory and a pkg, since we cd into tests_dir_modules/ambiguous
        os.chdir("tests_dir_modules/ambiguous")
        # pkg1 defaults to directory because tests_dir_modules/ambiguous/pkg1 exists
        lines = self.coverage_usepkgs(source=["pkg1"])
        self.filenames_in(lines, "ambiguous")
        self.filenames_not_in(lines, "p1a p1b p1c")

    def test_ambiguous_source_package_as_package(self):
        # pkg1 is a directory and a pkg, since we cd into tests_dir_modules/ambiguous
        os.chdir("tests_dir_modules/ambiguous")
        lines = self.coverage_usepkgs(source_pkgs=["pkg1"])
        self.filenames_in(lines, "p1a p1b")
        self.filenames_not_in(lines, "p2a p2b othera otherb osa osb ambiguous")
        # Because source= was specified, we do search for un-executed files.
        assert lines['p1c'] == 0


class ReportIncludeOmitTest(IncludeOmitTestsMixin, CoverageTest):
    """Tests of the report include/omit functionality."""

    def coverage_usepkgs(self, **kwargs):
        """Try coverage.report()."""
        cov = coverage.Coverage()
        cov.start()
        import usepkgs  # pragma: nested   # pylint: disable=import-error, unused-import
        cov.stop()      # pragma: nested
        report = io.StringIO()
        cov.report(file=report, **kwargs)
        return report.getvalue()


class XmlIncludeOmitTest(IncludeOmitTestsMixin, CoverageTest):
    """Tests of the XML include/omit functionality.

    This also takes care of the HTML and annotate include/omit, by virtue
    of the structure of the code.

    """

    def coverage_usepkgs(self, **kwargs):
        """Try coverage.xml_report()."""
        cov = coverage.Coverage()
        cov.start()
        import usepkgs  # pragma: nested   # pylint: disable=import-error, unused-import
        cov.stop()      # pragma: nested
        cov.xml_report(outfile="-", **kwargs)
        return self.stdout()


class AnalysisTest(CoverageTest):
    """Test the numerical analysis of results."""
    def test_many_missing_branches(self):
        cov = coverage.Coverage(branch=True)

        self.make_file("missing.py", """\
            def fun1(x):
                if x == 1:
                    print("one")
                else:
                    print("not one")
                print("done")           # pragma: nocover

            def fun2(x):
                print("x")

            fun2(3)
            """)

        # Import the Python file, executing it.
        self.start_import_stop(cov, "missing")

        nums = cov._analyze("missing.py").numbers
        assert nums.n_files == 1
        assert nums.n_statements == 7
        assert nums.n_excluded == 1
        assert nums.n_missing == 3
        assert nums.n_branches == 2
        assert nums.n_partial_branches == 0
        assert nums.n_missing_branches == 2


class TestRunnerPluginTest(CoverageTest):
    """Test that the API works properly the way various third-party plugins call it.

    We don't actually use the plugins, but these tests call the API the same
    way they do.

    """
    def pretend_to_be_nose_with_cover(self, erase=False, cd=False):
        """This is what the nose --with-cover plugin does."""
        self.make_file("no_biggie.py", """\
            a = 1
            b = 2
            if b == 1:
                c = 4
            """)
        self.make_file("sub/hold.txt", "")

        cov = coverage.Coverage()
        if erase:
            cov.combine()
            cov.erase()
        cov.load()
        self.start_import_stop(cov, "no_biggie")
        if cd:
            os.chdir("sub")
        cov.combine()
        cov.save()
        cov.report(["no_biggie.py"], show_missing=True)
        assert self.stdout() == textwrap.dedent("""\
            Name           Stmts   Miss  Cover   Missing
            --------------------------------------------
            no_biggie.py       4      1    75%   4
            --------------------------------------------
            TOTAL              4      1    75%
            """)
        if cd:
            os.chdir("..")

    def test_nose_plugin(self):
        self.pretend_to_be_nose_with_cover()

    def test_nose_plugin_with_erase(self):
        self.pretend_to_be_nose_with_cover(erase=True)

    def test_nose_plugin_with_cd(self):
        # https://github.com/nedbat/coveragepy/issues/916
        self.pretend_to_be_nose_with_cover(cd=True)

    def pretend_to_be_pytestcov(self, append):
        """Act like pytest-cov."""
        self.make_file("prog.py", """\
            a = 1
            b = 2
            if b == 1:
                c = 4
            """)
        self.make_file(".coveragerc", """\
            [run]
            parallel = True
            source = .
            """)

        cov = coverage.Coverage(source=None, branch=None, config_file='.coveragerc')
        if append:
            cov.load()
        else:
            cov.erase()
        self.start_import_stop(cov, "prog")
        cov.combine()
        cov.save()
        report = io.StringIO()
        cov.report(show_missing=None, ignore_errors=True, file=report, skip_covered=None,
                   skip_empty=None)
        assert report.getvalue() == textwrap.dedent("""\
            Name      Stmts   Miss  Cover
            -----------------------------
            prog.py       4      1    75%
            -----------------------------
            TOTAL         4      1    75%
            """)
        self.assert_file_count(".coverage", 0)
        self.assert_file_count(".coverage.*", 1)

    def test_pytestcov_parallel(self):
        self.pretend_to_be_pytestcov(append=False)

    def test_pytestcov_parallel_append(self):
        self.pretend_to_be_pytestcov(append=True)


class ImmutableConfigTest(CoverageTest):
    """Check that reporting methods don't permanently change the configuration."""
    def test_config_doesnt_change(self):
        self.make_file("simple.py", "a = 1")
        cov = coverage.Coverage()
        self.start_import_stop(cov, "simple")
        assert cov.get_option("report:show_missing") is False
        cov.report(show_missing=True)
        assert cov.get_option("report:show_missing") is False


class RelativePathTest(CoverageTest):
    """Tests of the relative_files setting."""
    def test_moving_stuff(self):
        # When using absolute file names, moving the source around results in
        # "No source for code" errors while reporting.
        self.make_file("foo.py", "a = 1")
        cov = coverage.Coverage(source=["."])
        self.start_import_stop(cov, "foo")
        res = cov.report()
        assert res == 100

        expected = re.escape("No source for code: '{}'.".format(abs_file("foo.py")))
        os.remove("foo.py")
        self.make_file("new/foo.py", "a = 1")
        shutil.move(".coverage", "new/.coverage")
        with change_dir("new"):
            cov = coverage.Coverage()
            cov.load()
            with pytest.raises(NoSource, match=expected):
                cov.report()

    def test_moving_stuff_with_relative(self):
        # When using relative file names, moving the source around is fine.
        self.make_file("foo.py", "a = 1")
        self.make_file(".coveragerc", """\
            [run]
            relative_files = true
            """)
        cov = coverage.Coverage(source=["."])
        self.start_import_stop(cov, "foo")
        res = cov.report()
        assert res == 100

        os.remove("foo.py")
        self.make_file("new/foo.py", "a = 1")
        shutil.move(".coverage", "new/.coverage")
        shutil.move(".coveragerc", "new/.coveragerc")
        with change_dir("new"):
            cov = coverage.Coverage()
            cov.load()
            res = cov.report()
            assert res == 100

    def test_combine_relative(self):
        self.make_file("foo.py", """\
            import mod
            a = 1
            """)
        self.make_file("lib/mod/__init__.py", "x = 1")
        self.make_file(".coveragerc", """\
            [run]
            relative_files = true
            """)
        sys.path.append("lib")
        cov = coverage.Coverage(source=["."], data_suffix=True)
        self.start_import_stop(cov, "foo")
        cov.save()

        self.make_file("dir2/bar.py", "a = 1")
        self.make_file("dir2/.coveragerc", """\
            [run]
            relative_files = true
            """)
        with change_dir("dir2"):
            cov = coverage.Coverage(source=["."], data_suffix=True)
            self.start_import_stop(cov, "bar")
            cov.save()
            shutil.move(glob.glob(".coverage.*")[0], "..")

        self.make_file("foo.py", "a = 1")
        self.make_file("bar.py", "a = 1")
        self.make_file("modsrc/__init__.py", "x = 1")

        self.make_file(".coveragerc", """\
            [run]
            relative_files = true
            [paths]
            source =
                modsrc
                */mod
            """)
        cov = coverage.Coverage()
        cov.combine()
        cov.save()

        cov = coverage.Coverage()
        cov.load()
        files = cov.get_data().measured_files()
        assert files == {'foo.py', 'bar.py', os_sep('modsrc/__init__.py')}
        res = cov.report()
        assert res == 100

    def test_combine_no_suffix_multiprocessing(self):
        self.make_file(".coveragerc", """\
            [run]
            branch = True
            """)
        cov = coverage.Coverage(
            config_file=".coveragerc",
            concurrency="multiprocessing",
            data_suffix=False,
        )
        cov.start()
        cov.stop()
        # The warning isn't the point of this test, but suppress it.
        with pytest.warns(Warning) as warns:
            cov.combine()
        assert_coverage_warnings(warns, "No data was collected. (no-data-collected)")
        cov.save()
        self.assert_file_count(".coverage.*", 0)
        self.assert_exists(".coverage")

    def test_files_up_one_level(self):
        # https://github.com/nedbat/coveragepy/issues/1280
        self.make_file("src/mycode.py", """\
            def foo():
                return 17
            """)
        self.make_file("test/test_it.py", """\
            from src.mycode import foo
            assert foo() == 17
            """)
        self.make_file("test/.coveragerc", """\
            [run]
            parallel = True
            relative_files = True

            [paths]
            source =
                ../src/
                */src
            """)
        os.chdir("test")
        sys.path.insert(0, "..")
        cov1 = coverage.Coverage()
        self.start_import_stop(cov1, "test_it")
        cov1.save()
        cov2 = coverage.Coverage()
        cov2.combine()
        cov3 = coverage.Coverage()
        cov3.load()
        report = self.get_report(cov3)
        assert self.last_line_squeezed(report) == "TOTAL 4 0 100%"


class CombiningTest(CoverageTest):
    """More tests of combining data."""

    B_LINES = {"b_or_c.py": [1, 2, 3, 4, 8, 9]}
    C_LINES = {"b_or_c.py": [1, 2, 3, 6, 7, 8, 9]}

    def make_b_or_c_py(self):
        """Create b_or_c.py, used in a few of these tests."""
        # "b_or_c.py b" will run 6 lines.
        # "b_or_c.py c" will run 7 lines.
        # Together, they run 8 lines.
        self.make_file("b_or_c.py", """\
            import sys
            a = 2
            if sys.argv[1] == 'b':
                b = 4
            else:
                c = 6
                c2 = 7
            d = 8
            print('done')
            """)

    def test_combine_parallel_data(self):
        self.make_b_or_c_py()
        self.make_data_file(".coverage.b", lines=self.B_LINES)
        self.make_data_file(".coverage.c", lines=self.C_LINES)

        # Combine the parallel coverage data files into .coverage .
        cov = coverage.Coverage()
        cov.combine(strict=True)
        self.assert_exists(".coverage")

        # After combining, there should be only the .coverage file.
        self.assert_file_count(".coverage.*", 0)

        # Read the coverage file and see that b_or_c.py has all 8 lines
        # executed.
        data = coverage.CoverageData()
        data.read()
        assert line_counts(data)['b_or_c.py'] == 8

        # Running combine again should fail, because there are no parallel data
        # files to combine.
        cov = coverage.Coverage()
        with pytest.raises(NoDataError, match=r"No data to combine"):
            cov.combine(strict=True)

        # And the originally combined data is still there.
        data = coverage.CoverageData()
        data.read()
        assert line_counts(data)['b_or_c.py'] == 8

    def test_combine_parallel_data_with_a_corrupt_file(self):
        self.make_b_or_c_py()
        self.make_data_file(".coverage.b", lines=self.B_LINES)
        self.make_data_file(".coverage.c", lines=self.C_LINES)

        # Make a bogus data file.
        self.make_file(".coverage.bad", "This isn't a coverage data file.")

        # Combine the parallel coverage data files into .coverage .
        cov = coverage.Coverage()
        with pytest.warns(Warning) as warns:
            cov.combine(strict=True)
        assert_coverage_warnings(
            warns,
            re.compile(
                r"Couldn't use data file '.*[/\\]\.coverage\.bad': " + BAD_SQLITE_REGEX
            ),
        )

        # After combining, those two should be the only data files.
        self.assert_exists(".coverage")
        self.assert_exists(".coverage.bad")
        self.assert_file_count(".coverage.*", 1)

        # Read the coverage file and see that b_or_c.py has all 8 lines
        # executed.
        data = coverage.CoverageData()
        data.read()
        assert line_counts(data)['b_or_c.py'] == 8

    def test_combine_no_usable_files(self):
        # https://github.com/nedbat/coveragepy/issues/629
        self.make_b_or_c_py()
        self.make_data_file(".coverage", lines=self.B_LINES)

        # Make bogus data files.
        self.make_file(".coverage.bad1", "This isn't a coverage data file.")
        self.make_file(".coverage.bad2", "This isn't a coverage data file either.")

        # Combine the parallel coverage data files into .coverage, but nothing is readable.
        cov = coverage.Coverage()
        with pytest.warns(Warning) as warns:
            with pytest.raises(NoDataError, match=r"No usable data files"):
                cov.combine(strict=True)

        warn_rx = re.compile(
            r"Couldn't use data file '.*[/\\]\.coverage\.bad[12]': " + BAD_SQLITE_REGEX
        )
        assert_coverage_warnings(warns, warn_rx, warn_rx)

        # After combining, we should have a main file and two parallel files.
        self.assert_exists(".coverage")
        self.assert_exists(".coverage.bad1")
        self.assert_exists(".coverage.bad2")
        self.assert_file_count(".coverage.*", 2)

        # Read the coverage file and see that b_or_c.py has 6 lines
        # executed (we only did b, not c).
        data = coverage.CoverageData()
        data.read()
        assert line_counts(data)['b_or_c.py'] == 6

    def test_combine_parallel_data_in_two_steps(self):
        self.make_b_or_c_py()
        self.make_data_file(".coverage.b", lines=self.B_LINES)

        # Combine the (one) parallel coverage data file into .coverage .
        cov = coverage.Coverage()
        cov.combine(strict=True)

        self.assert_exists(".coverage")
        self.assert_file_count(".coverage.*", 0)

        self.make_data_file(".coverage.c", lines=self.C_LINES)
        self.assert_exists(".coverage")
        self.assert_file_count(".coverage.*", 1)

        # Combine the parallel coverage data files into .coverage .
        cov = coverage.Coverage()
        cov.load()
        cov.combine(strict=True)

        # After combining, there should be only the .coverage file.
        self.assert_exists(".coverage")
        self.assert_file_count(".coverage.*", 0)

        # Read the coverage file and see that b_or_c.py has all 8 lines
        # executed.
        data = coverage.CoverageData()
        data.read()
        assert line_counts(data)['b_or_c.py'] == 8

    def test_combine_parallel_data_no_append(self):
        self.make_b_or_c_py()
        self.make_data_file(".coverage.b", lines=self.B_LINES)

        # Combine the (one) parallel coverage data file into .coverage .
        cov = coverage.Coverage()
        cov.combine(strict=True)
        self.assert_exists(".coverage")
        self.assert_file_count(".coverage.*", 0)

        self.make_data_file(".coverage.c", lines=self.C_LINES)

        # Combine the parallel coverage data files into .coverage, but don't
        # use the data in .coverage already.
        cov = coverage.Coverage()
        cov.combine(strict=True)

        # After combining, there should be only the .coverage file.
        self.assert_exists(".coverage")
        self.assert_file_count(".coverage.*", 0)

        # Read the coverage file and see that b_or_c.py has only 7 lines
        # because we didn't keep the data from running b.
        data = coverage.CoverageData()
        data.read()
        assert line_counts(data)['b_or_c.py'] == 7

    def test_combine_parallel_data_keep(self):
        self.make_b_or_c_py()
        self.make_data_file(".coverage.b", lines=self.B_LINES)
        self.make_data_file(".coverage.c", lines=self.C_LINES)

        # Combine the parallel coverage data files into .coverage with the keep flag.
        cov = coverage.Coverage()
        cov.combine(strict=True, keep=True)

        # After combining, the .coverage file & the original combined file should still be there.
        self.assert_exists(".coverage")
        self.assert_file_count(".coverage.*", 2)


class ReportMapsPathsTest(CoverageTest):
    """Check that reporting implicitly maps paths."""

    def make_files(self, data, settings=False):
        """Create the test files we need for line coverage."""
        src = """\
            if VER == 1:
                print("line 2")
            if VER == 2:
                print("line 4")
            if VER == 3:
                print("line 6")
            """
        self.make_file("src/program.py", src)
        self.make_file("ver1/program.py", src)
        self.make_file("ver2/program.py", src)

        if data == "line":
            self.make_data_file(
                lines={
                    abs_file("ver1/program.py"): [1, 2, 3, 5],
                    abs_file("ver2/program.py"): [1, 3, 4, 5],
                }
            )
        else:
            self.make_data_file(
                arcs={
                    abs_file("ver1/program.py"): arcz_to_arcs(".1 12 23 35 5."),
                    abs_file("ver2/program.py"): arcz_to_arcs(".1 13 34 45 5."),
                }
            )

        if settings:
            self.make_file(".coveragerc", """\
                [paths]
                source =
                    src
                    ver1
                    ver2
                """)

    def test_map_paths_during_line_report_without_setting(self):
        self.make_files(data="line")
        cov = coverage.Coverage()
        cov.load()
        cov.report(show_missing=True)
        expected = textwrap.dedent(os_sep("""\
            Name              Stmts   Miss  Cover   Missing
            -----------------------------------------------
            ver1/program.py       6      2    67%   4, 6
            ver2/program.py       6      2    67%   2, 6
            -----------------------------------------------
            TOTAL                12      4    67%
            """))
        assert expected == self.stdout()

    def test_map_paths_during_line_report(self):
        self.make_files(data="line", settings=True)
        cov = coverage.Coverage()
        cov.load()
        cov.report(show_missing=True)
        expected = textwrap.dedent(os_sep("""\
            Name             Stmts   Miss  Cover   Missing
            ----------------------------------------------
            src/program.py       6      1    83%   6
            ----------------------------------------------
            TOTAL                6      1    83%
            """))
        assert expected == self.stdout()

    def test_map_paths_during_branch_report_without_setting(self):
        self.make_files(data="arcs")
        cov = coverage.Coverage(branch=True)
        cov.load()
        cov.report(show_missing=True)
        expected = textwrap.dedent(os_sep("""\
            Name              Stmts   Miss Branch BrPart  Cover   Missing
            -------------------------------------------------------------
            ver1/program.py       6      2      6      3    58%   1->3, 4, 6
            ver2/program.py       6      2      6      3    58%   2, 3->5, 6
            -------------------------------------------------------------
            TOTAL                12      4     12      6    58%
            """))
        assert expected == self.stdout()

    def test_map_paths_during_branch_report(self):
        self.make_files(data="arcs", settings=True)
        cov = coverage.Coverage(branch=True)
        cov.load()
        cov.report(show_missing=True)
        expected = textwrap.dedent(os_sep("""\
            Name             Stmts   Miss Branch BrPart  Cover   Missing
            ------------------------------------------------------------
            src/program.py       6      1      6      1    83%   6
            ------------------------------------------------------------
            TOTAL                6      1      6      1    83%
            """))
        assert expected == self.stdout()

    def test_map_paths_during_annotate(self):
        self.make_files(data="line", settings=True)
        cov = coverage.Coverage()
        cov.load()
        cov.annotate()
        self.assert_exists(os_sep("src/program.py,cover"))
        self.assert_doesnt_exist(os_sep("ver1/program.py,cover"))
        self.assert_doesnt_exist(os_sep("ver2/program.py,cover"))

    def test_map_paths_during_html_report(self):
        self.make_files(data="line", settings=True)
        cov = coverage.Coverage()
        cov.load()
        cov.html_report()
        contains("htmlcov/index.html", os_sep("src/program.py"))
        doesnt_contain("htmlcov/index.html", os_sep("ver1/program.py"), os_sep("ver2/program.py"))

    def test_map_paths_during_xml_report(self):
        self.make_files(data="line", settings=True)
        cov = coverage.Coverage()
        cov.load()
        cov.xml_report()
        contains("coverage.xml", "src/program.py")
        doesnt_contain("coverage.xml", "ver1/program.py", "ver2/program.py")

    def test_map_paths_during_json_report(self):
        self.make_files(data="line", settings=True)
        cov = coverage.Coverage()
        cov.load()
        cov.json_report()
        def os_sepj(s):
            return os_sep(s).replace("\\", r"\\")
        contains("coverage.json", os_sepj("src/program.py"))
        doesnt_contain("coverage.json", os_sepj("ver1/program.py"), os_sepj("ver2/program.py"))

    def test_map_paths_during_lcov_report(self):
        self.make_files(data="line", settings=True)
        cov = coverage.Coverage()
        cov.load()
        cov.lcov_report()
        contains("coverage.lcov", os_sep("src/program.py"))
        doesnt_contain("coverage.lcov", os_sep("ver1/program.py"), os_sep("ver2/program.py"))
