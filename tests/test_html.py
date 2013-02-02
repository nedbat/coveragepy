# -*- coding: utf-8 -*-
"""Tests that HTML generation is awesome."""

import os.path, re, sys
import coverage
from coverage.misc import NotPython, NoSource

from test.coveragetest import CoverageTest

class HtmlTestHelpers(CoverageTest):
    """Methods that help with HTML tests."""

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

    def run_coverage(self, covargs=None, htmlargs=None):
        """Run coverage on main_file.py, and create an HTML report."""
        self.clean_local_file_imports()
        cov = coverage.coverage(**(covargs or {}))
        self.start_import_stop(cov, "main_file")
        cov.html_report(**(htmlargs or {}))

    def remove_html_files(self):
        """Remove the HTML files created as part of the HTML report."""
        os.remove("htmlcov/index.html")
        os.remove("htmlcov/main_file.html")
        os.remove("htmlcov/helper1.html")
        os.remove("htmlcov/helper2.html")


class HtmlDeltaTest(HtmlTestHelpers, CoverageTest):
    """Tests of the HTML delta speed-ups."""

    def setUp(self):
        super(HtmlDeltaTest, self).setUp()

        # At least one of our tests monkey-patches the version of coverage,
        # so grab it here to restore it later.
        self.real_coverage_version = coverage.__version__

        self.maxDiff = None

    def tearDown(self):
        coverage.__version__ = self.real_coverage_version
        super(HtmlDeltaTest, self).tearDown()

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
        self.run_coverage(covargs=dict(omit=[]))
        index1 = open("htmlcov/index.html").read()
        self.remove_html_files()

        self.run_coverage(covargs=dict(omit=['xyzzy*']))

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


class HtmlTitleTests(HtmlTestHelpers, CoverageTest):
    """Tests of the HTML title support."""

    def test_default_title(self):
        self.create_initial_files()
        self.run_coverage()
        index = open("htmlcov/index.html").read()
        self.assertIn("<title>Coverage report</title>", index)
        self.assertIn("<h1>Coverage report:", index)

    def test_title_set_in_config_file(self):
        self.create_initial_files()
        self.make_file(".coveragerc", "[html]\ntitle = Metrics & stuff!\n")
        self.run_coverage()
        index = open("htmlcov/index.html").read()
        self.assertIn("<title>Metrics &amp; stuff!</title>", index)
        self.assertIn("<h1>Metrics &amp; stuff!:", index)

    if sys.version_info[:2] != (3,1):
        def test_non_ascii_title_set_in_config_file(self):
            self.create_initial_files()
            self.make_file(".coveragerc",
                "[html]\ntitle = «ταБЬℓσ» numbers"
                )
            self.run_coverage()
            index = open("htmlcov/index.html").read()
            self.assertIn(
                "<title>&#171;&#964;&#945;&#1041;&#1068;&#8467;&#963;&#187;"
                " numbers", index
                )
            self.assertIn(
                "<h1>&#171;&#964;&#945;&#1041;&#1068;&#8467;&#963;&#187;"
                " numbers", index
                )

    def test_title_set_in_args(self):
        self.create_initial_files()
        self.make_file(".coveragerc", "[html]\ntitle = Good title\n")
        self.run_coverage(htmlargs=dict(title="«ταБЬℓσ» & stüff!"))
        index = open("htmlcov/index.html").read()
        self.assertIn(
            "<title>&#171;&#964;&#945;&#1041;&#1068;&#8467;&#963;&#187;"
            " &amp; st&#252;ff!</title>", index
            )
        self.assertIn(
            "<h1>&#171;&#964;&#945;&#1041;&#1068;&#8467;&#963;&#187;"
            " &amp; st&#252;ff!:", index
            )


class HtmlWithUnparsableFilesTest(CoverageTest):
    """Test the behavior when measuring unparsable files."""

    def test_dotpy_not_python(self):
        self.make_file("innocuous.py", "a = 1")
        cov = coverage.coverage()
        self.start_import_stop(cov, "innocuous")
        self.make_file("innocuous.py", "<h1>This isn't python!</h1>")
        self.assertRaisesRegexp(
            NotPython,
            "Couldn't parse '.*innocuous.py' as Python source: '.*' at line 1",
            cov.html_report
            )

    def test_dotpy_not_python_ignored(self):
        self.make_file("innocuous.py", "a = 2")
        cov = coverage.coverage()
        self.start_import_stop(cov, "innocuous")
        self.make_file("innocuous.py", "<h1>This isn't python!</h1>")
        cov.html_report(ignore_errors=True)
        self.assert_exists("htmlcov/index.html")
        # this would be better as a glob, if the html layout changes:
        self.assert_doesnt_exist("htmlcov/innocuous.html")

    def test_dothtml_not_python(self):
        # We run a .html file, and when reporting, we can't parse it as
        # Python.  Since it wasn't .py, no error is reported.

        # Run an "html" file
        self.make_file("innocuous.html", "a = 3")
        self.run_command("coverage run innocuous.html")
        # Before reporting, change it to be an HTML file.
        self.make_file("innocuous.html", "<h1>This isn't python at all!</h1>")
        output = self.run_command("coverage html")
        self.assertEqual(output.strip(), "No data to report.")

    def test_execed_liar_ignored(self):
        # Jinja2 sets __file__ to be a non-Python file, and then execs code.
        # If that file contains non-Python code, a TokenError shouldn't
        # have been raised when writing the HTML report.
        if sys.version_info < (3, 0):
            source = "exec compile('','','exec') in {'__file__': 'liar.html'}"
        else:
            source = "exec(compile('','','exec'), {'__file__': 'liar.html'})"
        self.make_file("liar.py", source)
        self.make_file("liar.html", "{# Whoops, not python code #}")
        cov = coverage.coverage()
        self.start_import_stop(cov, "liar")
        cov.html_report()
        self.assert_exists("htmlcov/index.html")

    def test_execed_liar_ignored_indentation_error(self):
        # Jinja2 sets __file__ to be a non-Python file, and then execs code.
        # If that file contains untokenizable code, we shouldn't get an
        # exception.
        if sys.version_info < (3, 0):
            source = "exec compile('','','exec') in {'__file__': 'liar.html'}"
        else:
            source = "exec(compile('','','exec'), {'__file__': 'liar.html'})"
        self.make_file("liar.py", source)
        # Tokenize will raise an IndentationError if it can't dedent.
        self.make_file("liar.html", "0\n  2\n 1\n")
        cov = coverage.coverage()
        self.start_import_stop(cov, "liar")
        cov.html_report()
        self.assert_exists("htmlcov/index.html")


class HtmlTest(CoverageTest):
    """Moar HTML tests."""

    def test_missing_source_file_incorrect_message(self):
        # https://bitbucket.org/ned/coveragepy/issue/60
        self.make_file("thefile.py", "import sub.another\n")
        self.make_file("sub/__init__.py", "")
        self.make_file("sub/another.py", "print('another')\n")
        cov = coverage.coverage()
        self.start_import_stop(cov, 'thefile')
        os.remove("sub/another.py")

        missing_file = os.path.join(self.temp_dir, "sub", "another.py")
        self.assertRaisesRegexp(NoSource,
            "(?i)No source for code: '%s'" % re.escape(missing_file),
            cov.html_report
            )
