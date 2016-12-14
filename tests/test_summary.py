# coding: utf8
# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

"""Test text-based summary reporting for coverage.py"""

import glob
import os
import os.path
import py_compile
import re
import sys

import coverage
from coverage import env
from coverage.backward import StringIO
from coverage.config import CoverageConfig
from coverage.control import Coverage
from coverage.data import CoverageData
from coverage.misc import CoverageException, output_encoding
from coverage.summary import SummaryReporter

from tests.coveragetest import CoverageTest

HERE = os.path.dirname(__file__)


class SummaryTest(CoverageTest):
    """Tests of the text summary reporting for coverage.py."""

    def setUp(self):
        super(SummaryTest, self).setUp()
        # Parent class saves and restores sys.path, we can just modify it.
        sys.path.append(self.nice_file(HERE, 'modules'))

    def make_mycode(self):
        """Make the mycode.py file when needed."""
        self.make_file("mycode.py", """\
            import covmod1
            import covmodzip1
            a = 1
            print('done')
            """)

    def test_report(self):
        self.make_mycode()
        out = self.run_command("coverage run mycode.py")
        self.assertEqual(out, 'done\n')
        report = self.report_from_command("coverage report")

        # Name                                           Stmts   Miss  Cover
        # ------------------------------------------------------------------
        # c:/ned/coverage/tests/modules/covmod1.py           2      0   100%
        # c:/ned/coverage/tests/zipmods.zip/covmodzip1.py    3      0   100%
        # mycode.py                                          4      0   100%
        # ------------------------------------------------------------------
        # TOTAL                                              9      0   100%

        self.assertNotIn("/coverage/__init__/", report)
        self.assertIn("/tests/modules/covmod1.py ", report)
        self.assertIn("/tests/zipmods.zip/covmodzip1.py ", report)
        self.assertIn("mycode.py ", report)
        self.assertEqual(self.last_line_squeezed(report), "TOTAL 9 0 100%")

    def test_report_just_one(self):
        # Try reporting just one module
        self.make_mycode()
        self.run_command("coverage run mycode.py")
        report = self.report_from_command("coverage report mycode.py")

        # Name        Stmts   Miss  Cover
        # -------------------------------
        # mycode.py       4      0   100%

        self.assertEqual(self.line_count(report), 3)
        self.assertNotIn("/coverage/", report)
        self.assertNotIn("/tests/modules/covmod1.py ", report)
        self.assertNotIn("/tests/zipmods.zip/covmodzip1.py ", report)
        self.assertIn("mycode.py ", report)
        self.assertEqual(self.last_line_squeezed(report), "mycode.py 4 0 100%")

    def test_report_wildcard(self):
        # Try reporting using wildcards to get the modules.
        self.make_mycode()
        self.run_command("coverage run mycode.py")
        report = self.report_from_command("coverage report my*.py")

        # Name        Stmts   Miss  Cover
        # -------------------------------
        # mycode.py       4      0   100%

        self.assertEqual(self.line_count(report), 3)
        self.assertNotIn("/coverage/", report)
        self.assertNotIn("/tests/modules/covmod1.py ", report)
        self.assertNotIn("/tests/zipmods.zip/covmodzip1.py ", report)
        self.assertIn("mycode.py ", report)
        self.assertEqual(self.last_line_squeezed(report), "mycode.py 4 0 100%")

    def test_report_omitting(self):
        # Try reporting while omitting some modules
        self.make_mycode()
        self.run_command("coverage run mycode.py")
        report = self.report_from_command("coverage report --omit '%s/*'" % HERE)

        # Name        Stmts   Miss  Cover
        # -------------------------------
        # mycode.py       4      0   100%

        self.assertEqual(self.line_count(report), 3)
        self.assertNotIn("/coverage/", report)
        self.assertNotIn("/tests/modules/covmod1.py ", report)
        self.assertNotIn("/tests/zipmods.zip/covmodzip1.py ", report)
        self.assertIn("mycode.py ", report)
        self.assertEqual(self.last_line_squeezed(report), "mycode.py 4 0 100%")

    def test_report_including(self):
        # Try reporting while including some modules
        self.make_mycode()
        self.run_command("coverage run mycode.py")
        report = self.report_from_command("coverage report --include=mycode*")

        # Name        Stmts   Miss  Cover
        # -------------------------------
        # mycode.py       4      0   100%

        self.assertEqual(self.line_count(report), 3)
        self.assertNotIn("/coverage/", report)
        self.assertNotIn("/tests/modules/covmod1.py ", report)
        self.assertNotIn("/tests/zipmods.zip/covmodzip1.py ", report)
        self.assertIn("mycode.py ", report)
        self.assertEqual(self.last_line_squeezed(report), "mycode.py 4 0 100%")

    def test_report_branches(self):
        self.make_file("mybranch.py", """\
            def branch(x):
                if x:
                    print("x")
                return x
            branch(1)
            """)
        out = self.run_command("coverage run --branch mybranch.py")
        self.assertEqual(out, 'x\n')
        report = self.report_from_command("coverage report")

        # Name          Stmts   Miss Branch BrPart  Cover
        # -----------------------------------------------
        # mybranch.py       5      0      2      1    85%

        self.assertEqual(self.line_count(report), 3)
        self.assertIn("mybranch.py ", report)
        self.assertEqual(self.last_line_squeezed(report), "mybranch.py 5 0 2 1 86%")

    def test_report_show_missing(self):
        self.make_file("mymissing.py", """\
            def missing(x, y):
                if x:
                    print("x")
                    return x
                if y:
                    print("y")
                try:
                    print("z")
                    1/0
                    print("Never!")
                except ZeroDivisionError:
                    pass
                return x
            missing(0, 1)
            """)
        out = self.run_command("coverage run mymissing.py")
        self.assertEqual(out, 'y\nz\n')
        report = self.report_from_command("coverage report --show-missing")

        # Name           Stmts   Miss  Cover   Missing
        # --------------------------------------------
        # mymissing.py      14      3    79%   3-4, 10

        self.assertEqual(self.line_count(report), 3)
        self.assertIn("mymissing.py ", report)
        self.assertEqual(self.last_line_squeezed(report), "mymissing.py 14 3 79% 3-4, 10")

    def test_report_show_missing_branches(self):
        self.make_file("mybranch.py", """\
            def branch(x, y):
                if x:
                    print("x")
                if y:
                    print("y")
            branch(1, 1)
            """)
        out = self.run_command("coverage run --branch mybranch.py")
        self.assertEqual(out, 'x\ny\n')
        report = self.report_from_command("coverage report --show-missing")

        # Name           Stmts   Miss Branch BrPart  Cover   Missing
        # ----------------------------------------------------------
        # mybranch.py        6      0      4      2    80%   2->4, 4->exit

        self.assertEqual(self.line_count(report), 3)
        self.assertIn("mybranch.py ", report)
        self.assertEqual(self.last_line_squeezed(report), "mybranch.py 6 0 4 2 80% 2->4, 4->exit")

    def test_report_show_missing_branches_and_lines(self):
        self.make_file("main.py", """\
            import mybranch
            """)
        self.make_file("mybranch.py", """\
            def branch(x, y, z):
                if x:
                    print("x")
                if y:
                    print("y")
                if z:
                    if x and y:
                        print("z")
                return x
            branch(1, 1, 0)
            """)
        out = self.run_command("coverage run --branch main.py")
        self.assertEqual(out, 'x\ny\n')
        report = self.report_from_command("coverage report --show-missing")
        report_lines = report.splitlines()

        expected = [
            'Name          Stmts   Miss Branch BrPart  Cover   Missing',
            '---------------------------------------------------------',
            'main.py           1      0      0      0   100%',
            'mybranch.py      10      2      8      3    61%   7-8, 2->4, 4->6, 6->7',
            '---------------------------------------------------------',
            'TOTAL            11      2      8      3    63%',
        ]
        self.assertEqual(report_lines, expected)

    def test_report_skip_covered_no_branches(self):
        self.make_file("main.py", """
            import not_covered

            def normal():
                print("z")
            normal()
        """)
        self.make_file("not_covered.py", """
            def not_covered():
                print("n")
        """)
        out = self.run_command("coverage run main.py")
        self.assertEqual(out, "z\n")
        report = self.report_from_command("coverage report --skip-covered --fail-under=70")

        # Name             Stmts   Miss  Cover
        # ------------------------------------
        # not_covered.py       2      1    50%
        # ------------------------------------
        # TOTAL                6      1    83%
        #
        # 1 file skipped due to complete coverage.

        self.assertEqual(self.line_count(report), 7, report)
        squeezed = self.squeezed_lines(report)
        self.assertEqual(squeezed[2], "not_covered.py 2 1 50%")
        self.assertEqual(squeezed[4], "TOTAL 6 1 83%")
        self.assertEqual(squeezed[6], "1 file skipped due to complete coverage.")
        self.assertEqual(self.last_command_status, 0)

    def test_report_skip_covered_branches(self):
        self.make_file("main.py", """
            import not_covered, covered

            def normal(z):
                if z:
                    print("z")
            normal(True)
            normal(False)
        """)
        self.make_file("not_covered.py", """
            def not_covered(n):
                if n:
                    print("n")
            not_covered(True)
        """)
        self.make_file("covered.py", """
            def foo():
                pass
            foo()
        """)
        out = self.run_command("coverage run --branch main.py")
        self.assertEqual(out, "n\nz\n")
        report = self.report_from_command("coverage report --skip-covered")

        # Name             Stmts   Miss Branch BrPart  Cover
        # --------------------------------------------------
        # not_covered.py       4      0      2      1    83%
        # --------------------------------------------------
        # TOTAL               13      0      4      1    94%
        #
        # 2 files skipped due to complete coverage.

        self.assertEqual(self.line_count(report), 7, report)
        squeezed = self.squeezed_lines(report)
        self.assertEqual(squeezed[2], "not_covered.py 4 0 2 1 83%")
        self.assertEqual(squeezed[4], "TOTAL 13 0 4 1 94%")
        self.assertEqual(squeezed[6], "2 files skipped due to complete coverage.")

    def test_report_skip_covered_branches_with_totals(self):
        self.make_file("main.py", """
            import not_covered
            import also_not_run

            def normal(z):
                if z:
                    print("z")
            normal(True)
            normal(False)
        """)
        self.make_file("not_covered.py", """
            def not_covered(n):
                if n:
                    print("n")
            not_covered(True)
        """)
        self.make_file("also_not_run.py", """
            def does_not_appear_in_this_film(ni):
                print("Ni!")
            """)
        out = self.run_command("coverage run --branch main.py")
        self.assertEqual(out, "n\nz\n")
        report = self.report_from_command("coverage report --skip-covered")

        # Name             Stmts   Miss Branch BrPart  Cover
        # --------------------------------------------------
        # also_not_run.py      2      1      0      0    50%
        # not_covered.py       4      0      2      1    83%
        # --------------------------------------------------
        # TOTAL                13     1      4      1    88%
        #
        # 1 file skipped due to complete coverage.

        self.assertEqual(self.line_count(report), 8, report)
        squeezed = self.squeezed_lines(report)
        self.assertEqual(squeezed[2], "also_not_run.py 2 1 0 0 50%")
        self.assertEqual(squeezed[3], "not_covered.py 4 0 2 1 83%")
        self.assertEqual(squeezed[5], "TOTAL 13 1 4 1 88%")
        self.assertEqual(squeezed[7], "1 file skipped due to complete coverage.")

    def test_report_skip_covered_all_files_covered(self):
        self.make_file("main.py", """
            def foo():
                pass
            foo()
        """)
        out = self.run_command("coverage run --branch main.py")
        self.assertEqual(out, "")
        report = self.report_from_command("coverage report --skip-covered")

        # Name      Stmts   Miss Branch BrPart  Cover
        # -------------------------------------------
        #
        # 1 file skipped due to complete coverage.

        self.assertEqual(self.line_count(report), 4, report)
        squeezed = self.squeezed_lines(report)
        self.assertEqual(squeezed[3], "1 file skipped due to complete coverage.")

    def test_report_skip_covered_longfilename(self):
        self.make_file("long_______________filename.py", """
            def foo():
                pass
            foo()
        """)
        out = self.run_command("coverage run --branch long_______________filename.py")
        self.assertEqual(out, "")
        report = self.report_from_command("coverage report --skip-covered")

        # Name    Stmts   Miss Branch BrPart  Cover
        # -----------------------------------------
        #
        # 1 file skipped due to complete coverage.

        self.assertEqual(self.line_count(report), 4, report)
        lines = self.report_lines(report)
        self.assertEqual(lines[0], "Name    Stmts   Miss Branch BrPart  Cover")
        squeezed = self.squeezed_lines(report)
        self.assertEqual(squeezed[3], "1 file skipped due to complete coverage.")

    def test_report_skip_covered_no_data(self):
        report = self.report_from_command("coverage report --skip-covered")

        # Name      Stmts   Miss Branch BrPart  Cover
        # -------------------------------------------
        # No data to report.

        self.assertEqual(self.line_count(report), 3, report)
        squeezed = self.squeezed_lines(report)
        self.assertEqual(squeezed[2], "No data to report.")

    def test_dotpy_not_python(self):
        # We run a .py file, and when reporting, we can't parse it as Python.
        # We should get an error message in the report.

        self.make_mycode()
        self.run_command("coverage run mycode.py")
        self.make_file("mycode.py", "This isn't python at all!")
        report = self.report_from_command("coverage report mycode.py")

        # mycode   NotPython: Couldn't parse '...' as Python source: 'invalid syntax' at line 1
        # Name     Stmts   Miss  Cover
        # ----------------------------
        # No data to report.

        errmsg = self.squeezed_lines(report)[0]
        # The actual file name varies run to run.
        errmsg = re.sub(r"parse '.*mycode.py", "parse 'mycode.py", errmsg)
        # The actual error message varies version to version
        errmsg = re.sub(r": '.*' at", ": 'error' at", errmsg)
        self.assertEqual(
            errmsg,
            "mycode.py NotPython: Couldn't parse 'mycode.py' as Python source: 'error' at line 1"
        )

    def test_accenteddotpy_not_python(self):
        # We run a .py file with a non-ascii name, and when reporting, we can't
        # parse it as Python.  We should get an error message in the report.

        self.make_file(u"accented\xe2.py", "print('accented')")
        self.run_command(u"coverage run accented\xe2.py")
        self.make_file(u"accented\xe2.py", "This isn't python at all!")
        report = self.report_from_command(u"coverage report accented\xe2.py")

        # xxxx   NotPython: Couldn't parse '...' as Python source: 'invalid syntax' at line 1
        # Name     Stmts   Miss  Cover
        # ----------------------------
        # No data to report.

        errmsg = self.squeezed_lines(report)[0]
        # The actual file name varies run to run.
        errmsg = re.sub(r"parse '.*(accented.*?\.py)", r"parse '\1", errmsg)
        # The actual error message varies version to version
        errmsg = re.sub(r": '.*' at", ": 'error' at", errmsg)
        expected = (
            u"accented\xe2.py NotPython: "
            u"Couldn't parse 'accented\xe2.py' as Python source: 'error' at line 1"
        )
        if env.PY2:
            # pylint: disable=redefined-variable-type
            expected = expected.encode(output_encoding())
        self.assertEqual(errmsg, expected)

    def test_dotpy_not_python_ignored(self):
        # We run a .py file, and when reporting, we can't parse it as Python,
        # but we've said to ignore errors, so there's no error reported.
        self.make_mycode()
        self.run_command("coverage run mycode.py")
        self.make_file("mycode.py", "This isn't python at all!")
        report = self.report_from_command("coverage report -i mycode.py")

        # Name     Stmts   Miss  Cover
        # ----------------------------

        self.assertEqual(self.line_count(report), 3)
        self.assertIn('No data to report.', report)

    def test_dothtml_not_python(self):
        # We run a .html file, and when reporting, we can't parse it as
        # Python.  Since it wasn't .py, no error is reported.

        # Run an "html" file
        self.make_file("mycode.html", "a = 1")
        self.run_command("coverage run mycode.html")
        # Before reporting, change it to be an HTML file.
        self.make_file("mycode.html", "<h1>This isn't python at all!</h1>")
        report = self.report_from_command("coverage report mycode.html")

        # Name     Stmts   Miss  Cover
        # ----------------------------
        # No data to report.

        self.assertEqual(self.line_count(report), 3)
        self.assertIn('No data to report.', report)

    def get_report(self, cov):
        """Get the report from `cov`, and canonicalize it."""
        repout = StringIO()
        cov.report(file=repout, show_missing=False)
        report = repout.getvalue().replace('\\', '/')
        report = re.sub(r" +", " ", report)
        return report

    def test_bug_156_file_not_run_should_be_zero(self):
        # https://bitbucket.org/ned/coveragepy/issue/156
        self.make_file("mybranch.py", """\
            def branch(x):
                if x:
                    print("x")
                return x
            branch(1)
            """)
        self.make_file("main.py", """\
            print("y")
            """)
        cov = coverage.Coverage(branch=True, source=["."])
        cov.start()
        import main     # pragma: nested # pylint: disable=import-error, unused-variable
        cov.stop()      # pragma: nested
        report = self.get_report(cov).splitlines()
        self.assertIn("mybranch.py 5 5 2 0 0%", report)

    def run_TheCode_and_report_it(self):
        """A helper for the next few tests."""
        cov = coverage.Coverage()
        cov.start()
        import TheCode  # pragma: nested # pylint: disable=import-error, unused-variable
        cov.stop()      # pragma: nested
        return self.get_report(cov)

    def test_bug_203_mixed_case_listed_twice_with_rc(self):
        self.make_file("TheCode.py", "a = 1\n")
        self.make_file(".coveragerc", "[run]\nsource = .\n")

        report = self.run_TheCode_and_report_it()

        self.assertIn("TheCode", report)
        self.assertNotIn("thecode", report)

    def test_bug_203_mixed_case_listed_twice(self):
        self.make_file("TheCode.py", "a = 1\n")

        report = self.run_TheCode_and_report_it()

        self.assertIn("TheCode", report)
        self.assertNotIn("thecode", report)

    def test_pyw_files(self):
        if not env.WINDOWS:
            self.skipTest(".pyw files are only on Windows.")

        # https://bitbucket.org/ned/coveragepy/issue/261
        self.make_file("start.pyw", """\
            import mod
            print("In start.pyw")
            """)
        self.make_file("mod.pyw", """\
            print("In mod.pyw")
            """)
        cov = coverage.Coverage()
        cov.start()
        import start    # pragma: nested # pylint: disable=import-error, unused-variable
        cov.stop()      # pragma: nested

        report = self.get_report(cov)
        self.assertNotIn("NoSource", report)
        report = report.splitlines()
        self.assertIn("start.pyw 2 0 100%", report)
        self.assertIn("mod.pyw 1 0 100%", report)

    def test_tracing_pyc_file(self):
        # Create two Python files.
        self.make_file("mod.py", "a = 1\n")
        self.make_file("main.py", "import mod\n")

        # Make one into a .pyc.
        py_compile.compile("mod.py")

        # Run the program.
        cov = coverage.Coverage()
        cov.start()
        import main     # pragma: nested # pylint: disable=import-error, unused-variable
        cov.stop()      # pragma: nested

        report = self.get_report(cov).splitlines()
        self.assertIn("mod.py 1 0 100%", report)

    def test_missing_py_file_during_run(self):
        # PyPy2 doesn't run bare .pyc files.
        if env.PYPY and env.PY2:
            self.skipTest("PyPy2 doesn't run bare .pyc files")

        # Create two Python files.
        self.make_file("mod.py", "a = 1\n")
        self.make_file("main.py", "import mod\n")

        # Make one into a .pyc, and remove the .py.
        py_compile.compile("mod.py")
        os.remove("mod.py")

        # Python 3 puts the .pyc files in a __pycache__ directory, and will
        # not import from there without source.  It will import a .pyc from
        # the source location though.
        if not os.path.exists("mod.pyc"):
            pycs = glob.glob("__pycache__/mod.*.pyc")
            self.assertEqual(len(pycs), 1)
            os.rename(pycs[0], "mod.pyc")

        # Run the program.
        cov = coverage.Coverage()
        cov.start()
        import main     # pragma: nested # pylint: disable=import-error, unused-variable
        cov.stop()      # pragma: nested

        # Put back the missing Python file.
        self.make_file("mod.py", "a = 1\n")
        report = self.get_report(cov).splitlines()
        self.assertIn("mod.py 1 0 100%", report)


class SummaryTest2(CoverageTest):
    """Another bunch of summary tests."""
    # This class exists because tests naturally clump into classes based on the
    # needs of their setUp, rather than the product features they are testing.
    # There's probably a better way to organize these.

    run_in_temp_dir = False

    def setUp(self):
        super(SummaryTest2, self).setUp()
        # Parent class saves and restores sys.path, we can just modify it.
        sys.path.append(self.nice_file(HERE, 'modules'))
        sys.path.append(self.nice_file(HERE, 'moremodules'))

    def test_empty_files(self):
        # Shows that empty files like __init__.py are listed as having zero
        # statements, not one statement.
        cov = coverage.Coverage(branch=True)
        cov.start()
        import usepkgs  # pragma: nested # pylint: disable=import-error, unused-variable
        cov.stop()      # pragma: nested

        repout = StringIO()
        cov.report(file=repout, show_missing=False)

        report = repout.getvalue().replace('\\', '/')
        report = re.sub(r"\s+", " ", report)
        self.assertIn("tests/modules/pkg1/__init__.py 2 0 0 0 100%", report)
        self.assertIn("tests/modules/pkg2/__init__.py 0 0 0 0 100%", report)


class ReportingReturnValueTest(CoverageTest):
    """Tests of reporting functions returning values."""

    def run_coverage(self):
        """Run coverage on doit.py and return the coverage object."""
        self.make_file("doit.py", """\
            a = 1
            b = 2
            c = 3
            d = 4
            if a > 10:
                f = 6
            g = 7
            """)

        cov = coverage.Coverage()
        self.start_import_stop(cov, "doit")
        return cov

    def test_report(self):
        cov = self.run_coverage()
        val = cov.report(include="*/doit.py")
        self.assertAlmostEqual(val, 85.7, 1)

    def test_html(self):
        cov = self.run_coverage()
        val = cov.html_report(include="*/doit.py")
        self.assertAlmostEqual(val, 85.7, 1)

    def test_xml(self):
        cov = self.run_coverage()
        val = cov.xml_report(include="*/doit.py")
        self.assertAlmostEqual(val, 85.7, 1)


class TestSummaryReporterConfiguration(CoverageTest):
    """Tests of SummaryReporter."""

    run_in_temp_dir = False

    # We just need some readable files to work with. These will do.
    HERE = os.path.dirname(__file__)

    LINES_1 = {
        os.path.join(HERE, "test_api.py"): dict.fromkeys(range(300)),
        os.path.join(HERE, "test_backward.py"): dict.fromkeys(range(20)),
        os.path.join(HERE, "test_coverage.py"): dict.fromkeys(range(15)),
    }

    def get_coverage_data(self, lines):
        """Get a CoverageData object that includes the requested lines."""
        data = CoverageData()
        data.add_lines(lines)
        return data

    def get_summary_text(self, coverage_data, options):
        """Get text output from the SummaryReporter."""
        cov = Coverage()
        cov.start()
        cov.stop()              # pragma: nested
        cov.data = coverage_data
        printer = SummaryReporter(cov, options)
        destination = StringIO()
        printer.report([], destination)
        return destination.getvalue()

    def test_test_data(self):
        # We use our own test files as test data. Check that our assumptions
        # about them are still valid.  We want the three columns of numbers to
        # sort in three different orders.
        data = self.get_coverage_data(self.LINES_1)
        report = self.get_summary_text(data, CoverageConfig())
        print(report)
        # Name                     Stmts   Miss  Cover
        # --------------------------------------------
        # tests/test_api.py          339    155    54%
        # tests/test_backward.py      13      3    77%
        # tests/test_coverage.py     234    228     3%
        # --------------------------------------------
        # TOTAL                      586    386    34%

        lines = report.splitlines()[2:-2]
        self.assertEqual(len(lines), 3)
        nums = [list(map(int, l.replace('%', '').split()[1:])) for l in lines]
        # [
        #  [339, 155, 54],
        #  [ 13,   3, 77],
        #  [234, 228,  3]
        # ]
        self.assertTrue(nums[1][0] < nums[2][0] < nums[0][0])
        self.assertTrue(nums[1][1] < nums[0][1] < nums[2][1])
        self.assertTrue(nums[2][2] < nums[0][2] < nums[1][2])

    def test_defaults(self):
        """Run the report with no configuration options."""
        data = self.get_coverage_data(self.LINES_1)
        opts = CoverageConfig()
        report = self.get_summary_text(data, opts)
        self.assertNotIn('Missing', report)
        self.assertNotIn('Branch', report)

    def test_print_missing(self):
        """Run the report printing the missing lines."""
        data = self.get_coverage_data(self.LINES_1)
        opts = CoverageConfig()
        opts.from_args(show_missing=True)
        report = self.get_summary_text(data, opts)
        self.assertIn('Missing', report)
        self.assertNotIn('Branch', report)

    def assert_ordering(self, text, *words):
        """Assert that the `words` appear in order in `text`."""
        indexes = list(map(text.find, words))
        self.assertEqual(
            indexes, sorted(indexes),
            "The words %r don't appear in order in %r" % (words, text)
        )

    def test_sort_report_by_stmts(self):
        # Sort the text report by the Stmts column.
        data = self.get_coverage_data(self.LINES_1)
        opts = CoverageConfig()
        opts.from_args(sort='Stmts')
        report = self.get_summary_text(data, opts)
        self.assert_ordering(report, "test_backward.py", "test_coverage.py", "test_api.py")

    def test_sort_report_by_cover(self):
        # Sort the text report by the Cover column.
        data = self.get_coverage_data(self.LINES_1)
        opts = CoverageConfig()
        opts.from_args(sort='Cover')
        report = self.get_summary_text(data, opts)
        self.assert_ordering(report, "test_coverage.py", "test_api.py", "test_backward.py")

    def test_sort_report_by_invalid_option(self):
        # Sort the text report by a nonsense column.
        data = self.get_coverage_data(self.LINES_1)
        opts = CoverageConfig()
        opts.from_args(sort='Xyzzy')
        msg = "Invalid sorting option: 'Xyzzy'"
        with self.assertRaisesRegex(CoverageException, msg):
            self.get_summary_text(data, opts)
