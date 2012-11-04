"""Test text-based summary reporting for coverage.py"""

import os, re, sys

import coverage
from coverage.backward import StringIO

sys.path.insert(0, os.path.split(__file__)[0]) # Force relative import for Py3k
from coveragetest import CoverageTest

class SummaryTest(CoverageTest):
    """Tests of the text summary reporting for coverage.py."""

    def setUp(self):
        super(SummaryTest, self).setUp()
        self.make_file("mycode.py", """\
            import covmod1
            import covmodzip1
            a = 1
            print ('done')
            """)
        # Parent class saves and restores sys.path, we can just modify it.
        sys.path.append(self.nice_file(os.path.dirname(__file__), 'modules'))

    def report_from_command(self, cmd):
        """Return the report from the `cmd`, with some convenience added."""
        report = self.run_command(cmd).replace('\\', '/')
        self.assertFalse("error" in report.lower())
        return report

    def line_count(self, report):
        """How many lines are in `report`?"""
        self.assertEqual(report.split('\n')[-1], "")
        return len(report.split('\n')) - 1

    def last_line_squeezed(self, report):
        """Return the last line of `report` with the spaces squeezed down."""
        last_line = report.split('\n')[-2]
        return re.sub(r"\s+", " ", last_line)

    def test_report(self):
        out = self.run_command("coverage -x mycode.py")
        self.assertEqual(out, 'done\n')
        report = self.report_from_command("coverage -r")

        # Name                                              Stmts   Miss  Cover
        # ---------------------------------------------------------------------
        # c:/ned/coverage/trunk/test/modules/covmod1            2      0   100%
        # c:/ned/coverage/trunk/test/zipmods.zip/covmodzip1     2      0   100%
        # mycode                                                4      0   100%
        # ---------------------------------------------------------------------
        # TOTAL                                                 8      0   100%

        self.assertFalse("/coverage/__init__/" in report)
        self.assertTrue("/test/modules/covmod1 " in report)
        self.assertTrue("/test/zipmods.zip/covmodzip1 " in report)
        self.assertTrue("mycode " in report)
        self.assertEqual(self.last_line_squeezed(report), "TOTAL 8 0 100%")

    def test_report_just_one(self):
        # Try reporting just one module
        self.run_command("coverage -x mycode.py")
        report = self.report_from_command("coverage -r mycode.py")

        # Name     Stmts   Miss  Cover
        # ----------------------------
        # mycode       4      0   100%

        self.assertEqual(self.line_count(report), 3)
        self.assertFalse("/coverage/" in report)
        self.assertFalse("/test/modules/covmod1 " in report)
        self.assertFalse("/test/zipmods.zip/covmodzip1 " in report)
        self.assertTrue("mycode " in report)
        self.assertEqual(self.last_line_squeezed(report), "mycode 4 0 100%")

    def test_report_omitting(self):
        # Try reporting while omitting some modules
        prefix = os.path.split(__file__)[0]
        self.run_command("coverage -x mycode.py")
        report = self.report_from_command("coverage -r -o '%s/*'" % prefix)

        # Name     Stmts   Miss  Cover
        # ----------------------------
        # mycode       4      0   100%

        self.assertEqual(self.line_count(report), 3)
        self.assertFalse("/coverage/" in report)
        self.assertFalse("/test/modules/covmod1 " in report)
        self.assertFalse("/test/zipmods.zip/covmodzip1 " in report)
        self.assertTrue("mycode " in report)
        self.assertEqual(self.last_line_squeezed(report), "mycode 4 0 100%")

    def test_report_including(self):
        # Try reporting while including some modules
        self.run_command("coverage run mycode.py")
        report = self.report_from_command("coverage report --include=mycode*")

        # Name     Stmts   Miss  Cover
        # ----------------------------
        # mycode       4      0   100%

        self.assertEqual(self.line_count(report), 3)
        self.assertFalse("/coverage/" in report)
        self.assertFalse("/test/modules/covmod1 " in report)
        self.assertFalse("/test/zipmods.zip/covmodzip1 " in report)
        self.assertTrue("mycode " in report)
        self.assertEqual(self.last_line_squeezed(report), "mycode 4 0 100%")

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

        # Name       Stmts   Miss Branch BrPart  Cover
        # --------------------------------------------
        # mybranch       5      0      2      1    85%

        self.assertEqual(self.line_count(report), 3)
        self.assertTrue("mybranch " in report)
        self.assertEqual(self.last_line_squeezed(report),
                                                        "mybranch 5 0 2 1 86%")

    def test_dotpy_not_python(self):
        # We run a .py file, and when reporting, we can't parse it as Python.
        # We should get an error message in the report.

        self.run_command("coverage run mycode.py")
        self.make_file("mycode.py", "This isn't python at all!")
        report = self.report_from_command("coverage -r mycode.py")

        # Name     Stmts   Miss  Cover
        # ----------------------------
        # mycode   NotPython: Couldn't parse '/tmp/test_cover/63354509363/mycode.py' as Python source: 'invalid syntax' at line 1

        last = self.last_line_squeezed(report)
        # The actual file name varies run to run.
        last = re.sub("parse '.*mycode.py", "parse 'mycode.py", last)
        # The actual error message varies version to version
        last = re.sub(": '.*' at", ": 'error' at", last)
        self.assertEqual(last,
            "mycode NotPython: "
            "Couldn't parse 'mycode.py' as Python source: "
            "'error' at line 1"
            )

    def test_dotpy_not_python_ignored(self):
        # We run a .py file, and when reporting, we can't parse it as Python,
        # but we've said to ignore errors, so there's no error reported.
        self.run_command("coverage run mycode.py")
        self.make_file("mycode.py", "This isn't python at all!")
        report = self.report_from_command("coverage -r -i mycode.py")

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
        report = self.report_from_command("coverage -r mycode.html")

        # Name     Stmts   Miss  Cover
        # ----------------------------

        self.assertEqual(self.line_count(report), 2)


class SummaryTest2(CoverageTest):
    """Another bunch of summary tests."""
    # This class exists because tests naturally clump into classes based on the
    # needs of their setUp and tearDown, rather than the product features they
    # are testing.  There's probably a better way to organize these.

    run_in_temp_dir = False

    def setUp(self):
        super(SummaryTest2, self).setUp()
        # Parent class saves and restores sys.path, we can just modify it.
        this_dir = os.path.dirname(__file__)
        sys.path.append(self.nice_file(this_dir, 'modules'))
        sys.path.append(self.nice_file(this_dir, 'moremodules'))

    def test_empty_files(self):
        # Shows that empty files like __init__.py are listed as having zero
        # statements, not one statement.
        cov = coverage.coverage()
        cov.start()
        import usepkgs                      # pylint: disable=F0401,W0612
        cov.stop()

        repout = StringIO()
        cov.report(file=repout, show_missing=False)

        report = repout.getvalue().replace('\\', '/')
        report = re.sub(r"\s+", " ", report)
        self.assert_("test/modules/pkg1/__init__ 1 0 100%" in report)
        self.assert_("test/modules/pkg2/__init__ 0 0 100%" in report)


class ReportingReturnValue(CoverageTest):
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
        cov.start()
        self.import_local_file("doit")
        cov.stop()
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
