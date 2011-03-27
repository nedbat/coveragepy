"""Tests that HTML generation is awesome."""

import os.path, sys
import coverage
sys.path.insert(0, os.path.split(__file__)[0]) # Force relative import for Py3k
from coveragetest import CoverageTest

class HtmlTest(CoverageTest):
    """HTML!"""

    def setUp(self):
        super(HtmlTest, self).setUp()

        # At least one of our tests monkey-patches the version of coverage,
        # so grab it here to restore it later.
        self.real_coverage_version = coverage.__version__

    def tearDown(self):
        coverage.__version__ = self.real_coverage_version
        super(HtmlTest, self).tearDown()

    def create_initial_files(self):
        """Create the source files we need to run these tests."""
        self.make_file("main_file.py", """\
            import helper1, helper2
            helper1.func1(12)
            helper2.func2(12)
            """)
        self.make_file("helper1.py", """\
            def func1(x):
                if x % 2:
                    print("odd")
            """)
        self.make_file("helper2.py", """\
            def func2(x):
                print("x is %d" % x)
            """)

    def run_coverage(self, **kwargs):
        """Run coverage on main_file.py, and create an HTML report."""
        self.clean_local_file_imports()
        cov = coverage.coverage(**kwargs)
        cov.start()
        self.import_local_file("main_file")
        cov.stop()
        cov.html_report()

    def remove_html_files(self):
        """Remove the HTML files created as part of the HTML report."""
        os.remove("htmlcov/index.html")
        os.remove("htmlcov/main_file.html")
        os.remove("htmlcov/helper1.html")
        os.remove("htmlcov/helper2.html")

    def test_html_created(self):
        # Test basic HTML generation: files should be created.
        self.create_initial_files()
        self.run_coverage()

        self.assert_exists("htmlcov/index.html")
        self.assert_exists("htmlcov/main_file.html")
        self.assert_exists("htmlcov/helper1.html")
        self.assert_exists("htmlcov/helper2.html")
        self.assert_exists("htmlcov/style.css")
        self.assert_exists("htmlcov/coverage_html.js")

    def test_html_delta_from_source_change(self):
        # HTML generation can create only the files that have changed.
        # In this case, helper1 changes because its source is different.
        self.create_initial_files()
        self.run_coverage()
        index1 = open("htmlcov/index.html").read()
        self.remove_html_files()

        # Now change a file and do it again
        self.make_file("helper1.py", """\
            def func1(x):   # A nice function
                if x % 2:
                    print("odd")
            """)

        self.run_coverage()

        # Only the changed files should have been created.
        self.assert_exists("htmlcov/index.html")
        self.assert_exists("htmlcov/helper1.html")
        self.assert_doesnt_exist("htmlcov/main_file.html")
        self.assert_doesnt_exist("htmlcov/helper2.html")
        index2 = open("htmlcov/index.html").read()
        self.assertMultiLineEqual(index1, index2)

    def test_html_delta_from_coverage_change(self):
        # HTML generation can create only the files that have changed.
        # In this case, helper1 changes because its coverage is different.
        self.create_initial_files()
        self.run_coverage()
        self.remove_html_files()

        # Now change a file and do it again
        self.make_file("main_file.py", """\
            import helper1, helper2
            helper1.func1(23)
            helper2.func2(23)
            """)

        self.run_coverage()

        # Only the changed files should have been created.
        self.assert_exists("htmlcov/index.html")
        self.assert_exists("htmlcov/helper1.html")
        self.assert_exists("htmlcov/main_file.html")
        self.assert_doesnt_exist("htmlcov/helper2.html")

    def test_html_delta_from_settings_change(self):
        # HTML generation can create only the files that have changed.
        # In this case, everything changes because the coverage settings have
        # changed.
        self.create_initial_files()
        self.run_coverage()
        index1 = open("htmlcov/index.html").read()
        self.remove_html_files()

        self.run_coverage(timid=True)

        # All the files have been reported again.
        self.assert_exists("htmlcov/index.html")
        self.assert_exists("htmlcov/helper1.html")
        self.assert_exists("htmlcov/main_file.html")
        self.assert_exists("htmlcov/helper2.html")
        index2 = open("htmlcov/index.html").read()
        self.assertMultiLineEqual(index1, index2)

    def test_html_delta_from_coverage_version_change(self):
        # HTML generation can create only the files that have changed.
        # In this case, everything changes because the coverage version has
        # changed.
        self.create_initial_files()
        self.run_coverage()
        index1 = open("htmlcov/index.html").read()
        self.remove_html_files()

        # "Upgrade" coverage.py!
        coverage.__version__ = "XYZZY"

        self.run_coverage()

        # All the files have been reported again.
        self.assert_exists("htmlcov/index.html")
        self.assert_exists("htmlcov/helper1.html")
        self.assert_exists("htmlcov/main_file.html")
        self.assert_exists("htmlcov/helper2.html")
        index2 = open("htmlcov/index.html").read()
        fixed_index2 = index2.replace("XYZZY", self.real_coverage_version)
        self.assertMultiLineEqual(index1, fixed_index2)

