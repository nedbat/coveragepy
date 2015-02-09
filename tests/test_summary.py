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

from tests.coveragetest import CoverageTest

HERE = os.path.dirname(__file__)


class SummaryTest(CoverageTest):
    """Tests of the text summary reporting for coverage.py."""

    def setUp(self):
        super(SummaryTest, self).setUp()
        self.make_file("mycode.py", """\
            import covmod1
            import covmodzip1
            a = 1
            print('done')
            """)
        # Parent class saves and restores sys.path, we can just modify it.
        sys.path.append(self.nice_file(HERE, 'modules'))

    def test_report(self):
        out = self.run_command("coverage run mycode.py")
        self.assertEqual(out, 'done\n')
        report = self.report_from_command("coverage report")

        # Name                                           Stmts   Miss  Cover
        # ------------------------------------------------------------------
        # c:/ned/coverage/tests/modules/covmod1.py           2      0   100%
        # c:/ned/coverage/tests/zipmods.zip/covmodzip1.py    2      0   100%
        # mycode.py                                          4      0   100%
        # ------------------------------------------------------------------
        # TOTAL                                              8      0   100%

        self.assertNotIn("/coverage/__init__/", report)
        self.assertIn("/tests/modules/covmod1.py ", report)
        self.assertIn("/tests/zipmods.zip/covmodzip1.py ", report)
        self.assertIn("mycode.py ", report)
        self.assertEqual(self.last_line_squeezed(report), "TOTAL 8 0 100%")

    def test_report_just_one(self):
        # Try reporting just one module
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
        self.run_command("coverage run mycode.py")
        report = self.report_from_command(
                    "coverage report --omit '%s/*'" % HERE
                    )

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
        self.assertEqual(self.last_line_squeezed(report),
                                "mybranch.py 5 0 2 1 86%")

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
        self.assertEqual(self.last_line_squeezed(report),
                         "mymissing.py 14 3 79% 3-4, 10")

    def test_report_show_missing_branches(self):
        self.make_file("mybranch.py", """\
            def branch(x, y):
                if x:
                    print("x")
                if y:
                    print("y")
                return x
            branch(1, 1)
            """)
        out = self.run_command("coverage run --branch mybranch.py")
        self.assertEqual(out, 'x\ny\n')
        report = self.report_from_command("coverage report --show-missing")

        # Name           Stmts   Miss Branch BrPart  Cover   Missing
        # ----------------------------------------------------------
        # mybranch.py        7      0      4      2    82%   2->4, 4->6

        self.assertEqual(self.line_count(report), 3)
        self.assertIn("mybranch.py ", report)
        self.assertEqual(self.last_line_squeezed(report),
                         "mybranch.py 7 0 4 2 82% 2->4, 4->6")

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

        # Name        Stmts   Miss Branch BrPart  Cover   Missing
        # -------------------------------------------------------
        # main.py         1      0      0      0   100%
        # mybranch.py    10      2      8      3    61%   7-8, 2->4, 4->6, 6->7
        # -------------------------------------------------------
        # TOTAL          11      2      8      3    63%

        self.assertEqual(self.line_count(report), 6)
        squeezed = self.squeezed_lines(report)
        self.assertEqual(
            squeezed[2],
            "main.py 1 0 0 0 100%"
        )
        self.assertEqual(
            squeezed[3],
            "mybranch.py 10 2 8 3 61% 7-8, 2->4, 4->6, 6->7"
        )
        self.assertEqual(
            squeezed[5],
            "TOTAL 11 2 8 3 63%"
        )

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
        report = self.report_from_command("coverage report --skip-covered")

        # Name             Stmts   Miss  Cover
        # ------------------------------------
        # not_covered.py       2      1    50%

        self.assertEqual(self.line_count(report), 3, report)
        squeezed = self.squeezed_lines(report)
        self.assertEqual(squeezed[2], "not_covered.py 2 1 50%")

    def test_report_skip_covered_branches(self):
        self.make_file("main.py", """
            import not_covered

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
        out = self.run_command("coverage run --branch main.py")
        self.assertEqual(out, "n\nz\n")
        report = self.report_from_command("coverage report --skip-covered")

        # Name             Stmts   Miss Branch BrPart  Cover
        # --------------------------------------------------
        # not_covered.py       4      0      2      1    83%

        self.assertEqual(self.line_count(report), 3, report)
        squeezed = self.squeezed_lines(report)
        self.assertEqual(squeezed[2], "not_covered.py 4 0 2 1 83%")

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
        # TOTAL                6      1      2      1    75%

        self.assertEqual(self.line_count(report), 6, report)
        squeezed = self.squeezed_lines(report)
        self.assertEqual(squeezed[2], "also_not_run.py 2 1 0 0 50%")
        self.assertEqual(squeezed[3], "not_covered.py 4 0 2 1 83%")
        self.assertEqual(squeezed[5], "TOTAL 6 1 2 1 75%")

    def test_dotpy_not_python(self):
        # We run a .py file, and when reporting, we can't parse it as Python.
        # We should get an error message in the report.

        self.run_command("coverage run mycode.py")
        self.make_file("mycode.py", "This isn't python at all!")
        report = self.report_from_command("coverage report mycode.py")

        # pylint: disable=line-too-long
        # Name     Stmts   Miss  Cover
        # ----------------------------
        # mycode   NotPython: Couldn't parse '/tmp/test_cover/63354509363/mycode.py' as Python source: 'invalid syntax' at line 1

        last = self.last_line_squeezed(report)
        # The actual file name varies run to run.
        last = re.sub(r"parse '.*mycode.py", "parse 'mycode.py", last)
        # The actual error message varies version to version
        last = re.sub(r": '.*' at", ": 'error' at", last)
        self.assertEqual(last,
            "mycode.py NotPython: "
            "Couldn't parse 'mycode.py' as Python source: "
            "'error' at line 1"
            )

    def test_dotpy_not_python_ignored(self):
        # We run a .py file, and when reporting, we can't parse it as Python,
        # but we've said to ignore errors, so there's no error reported.
        self.run_command("coverage run mycode.py")
        self.make_file("mycode.py", "This isn't python at all!")
        report = self.report_from_command("coverage report -i mycode.py")

        # Name     Stmts   Miss  Cover
        # ----------------------------

        self.assertEqual(self.line_count(report), 2)

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

        self.assertEqual(self.line_count(report), 2)

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
        cov = coverage.coverage(branch=True, source=["."])
        cov.start()
        import main     # pragma: nested # pylint: disable=import-error,unused-variable
        cov.stop()      # pragma: nested
        report = self.get_report(cov).splitlines()
        self.assertIn("mybranch.py 5 5 2 0 0%", report)

    def run_TheCode_and_report_it(self):
        """A helper for the next few tests."""
        cov = coverage.coverage()
        cov.start()
        import TheCode  # pragma: nested # pylint: disable=import-error,unused-variable
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
            self.skip(".pyw files are only on Windows.")

        # https://bitbucket.org/ned/coveragepy/issue/261
        self.make_file("start.pyw", """\
            import mod
            print("In start.pyw")
            """)
        self.make_file("mod.pyw", """\
            print("In mod.pyw")
            """)
        cov = coverage.coverage()
        cov.start()
        import start    # pragma: nested # pylint: disable=import-error,unused-variable
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
        cov = coverage.coverage()
        cov.start()
        import main     # pragma: nested # pylint: disable=import-error,unused-variable
        cov.stop()      # pragma: nested

        report = self.get_report(cov).splitlines()
        self.assertIn("mod.py 1 0 100%", report)

    def test_missing_py_file_during_run(self):
        # PyPy2 doesn't run bare .pyc files.
        if env.PYPY and env.PY2:
            self.skip("PyPy2 doesn't run bare .pyc files")

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
        cov = coverage.coverage()
        cov.start()
        import main     # pragma: nested # pylint: disable=import-error,unused-variable
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
        cov = coverage.coverage()
        cov.start()
        import usepkgs  # pragma: nested # pylint: disable=import-error,unused-variable
        cov.stop()      # pragma: nested

        repout = StringIO()
        cov.report(file=repout, show_missing=False)

        report = repout.getvalue().replace('\\', '/')
        report = re.sub(r"\s+", " ", report)
        self.assertIn("tests/modules/pkg1/__init__.py 1 0 100%", report)
        self.assertIn("tests/modules/pkg2/__init__.py 0 0 100%", report)


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

        cov = coverage.coverage()
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
