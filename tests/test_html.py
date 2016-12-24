# -*- coding: utf-8 -*-
# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

"""Tests that HTML generation is awesome."""

import datetime
import glob
import json
import os
import os.path
import re
import sys

import coverage
import coverage.files
import coverage.html
from coverage.misc import CoverageException, NotPython, NoSource

from tests.coveragetest import CoverageTest
from tests.goldtest import CoverageGoldTest
from tests.goldtest import change_dir, compare, contains, doesnt_contain, contains_any


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
        """Run coverage.py on main_file.py, and create an HTML report."""
        self.clean_local_file_imports()
        cov = coverage.Coverage(**(covargs or {}))
        self.start_import_stop(cov, "main_file")
        cov.html_report(**(htmlargs or {}))

    def remove_html_files(self):
        """Remove the HTML files created as part of the HTML report."""
        os.remove("htmlcov/index.html")
        os.remove("htmlcov/main_file_py.html")
        os.remove("htmlcov/helper1_py.html")
        os.remove("htmlcov/helper2_py.html")

    def get_html_report_content(self, module):
        """Return the content of the HTML report for `module`."""
        filename = module.replace(".", "_").replace("/", "_") + ".html"
        filename = os.path.join("htmlcov", filename)
        with open(filename) as f:
            return f.read()

    def get_html_index_content(self):
        """Return the content of index.html.

        Timestamps are replaced with a placeholder so that clocks don't matter.

        """
        with open("htmlcov/index.html") as f:
            index = f.read()
        index = re.sub(
            r"created at \d{4}-\d{2}-\d{2} \d{2}:\d{2}",
            r"created at YYYY-MM-DD HH:MM",
            index,
        )
        return index

    def assert_correct_timestamp(self, html):
        """Extract the timestamp from `html`, and assert it is recent."""
        timestamp_pat = r"created at (\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})"
        m = re.search(timestamp_pat, html)
        self.assertTrue(m, "Didn't find a timestamp!")
        timestamp = datetime.datetime(*map(int, m.groups()))
        # The timestamp only records the minute, so the delta could be from
        # 12:00 to 12:01:59, or two minutes.
        self.assert_recent_datetime(
            timestamp,
            seconds=120,
            msg="Timestamp is wrong: {0}".format(timestamp),
        )


class HtmlDeltaTest(HtmlTestHelpers, CoverageTest):
    """Tests of the HTML delta speed-ups."""

    def setUp(self):
        super(HtmlDeltaTest, self).setUp()

        # At least one of our tests monkey-patches the version of coverage.py,
        # so grab it here to restore it later.
        self.real_coverage_version = coverage.__version__
        self.addCleanup(self.cleanup_coverage_version)

    def cleanup_coverage_version(self):
        """A cleanup."""
        coverage.__version__ = self.real_coverage_version

    def test_html_created(self):
        # Test basic HTML generation: files should be created.
        self.create_initial_files()
        self.run_coverage()

        self.assert_exists("htmlcov/index.html")
        self.assert_exists("htmlcov/main_file_py.html")
        self.assert_exists("htmlcov/helper1_py.html")
        self.assert_exists("htmlcov/helper2_py.html")
        self.assert_exists("htmlcov/style.css")
        self.assert_exists("htmlcov/coverage_html.js")

    def test_html_delta_from_source_change(self):
        # HTML generation can create only the files that have changed.
        # In this case, helper1 changes because its source is different.
        self.create_initial_files()
        self.run_coverage()
        index1 = self.get_html_index_content()
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
        self.assert_exists("htmlcov/helper1_py.html")
        self.assert_doesnt_exist("htmlcov/main_file_py.html")
        self.assert_doesnt_exist("htmlcov/helper2_py.html")
        index2 = self.get_html_index_content()
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
        self.assert_exists("htmlcov/helper1_py.html")
        self.assert_exists("htmlcov/main_file_py.html")
        self.assert_doesnt_exist("htmlcov/helper2_py.html")

    def test_html_delta_from_settings_change(self):
        # HTML generation can create only the files that have changed.
        # In this case, everything changes because the coverage.py settings
        # have changed.
        self.create_initial_files()
        self.run_coverage(covargs=dict(omit=[]))
        index1 = self.get_html_index_content()
        self.remove_html_files()

        self.run_coverage(covargs=dict(omit=['xyzzy*']))

        # All the files have been reported again.
        self.assert_exists("htmlcov/index.html")
        self.assert_exists("htmlcov/helper1_py.html")
        self.assert_exists("htmlcov/main_file_py.html")
        self.assert_exists("htmlcov/helper2_py.html")
        index2 = self.get_html_index_content()
        self.assertMultiLineEqual(index1, index2)

    def test_html_delta_from_coverage_version_change(self):
        # HTML generation can create only the files that have changed.
        # In this case, everything changes because the coverage.py version has
        # changed.
        self.create_initial_files()
        self.run_coverage()
        index1 = self.get_html_index_content()
        self.remove_html_files()

        # "Upgrade" coverage.py!
        coverage.__version__ = "XYZZY"

        self.run_coverage()

        # All the files have been reported again.
        self.assert_exists("htmlcov/index.html")
        self.assert_exists("htmlcov/helper1_py.html")
        self.assert_exists("htmlcov/main_file_py.html")
        self.assert_exists("htmlcov/helper2_py.html")
        index2 = self.get_html_index_content()
        fixed_index2 = index2.replace("XYZZY", self.real_coverage_version)
        self.assertMultiLineEqual(index1, fixed_index2)

    def test_status_format_change(self):
        self.create_initial_files()
        self.run_coverage()
        self.remove_html_files()

        with open("htmlcov/status.json") as status_json:
            status_data = json.load(status_json)

        self.assertEqual(status_data['format'], 1)
        status_data['format'] = 2
        with open("htmlcov/status.json", "w") as status_json:
            json.dump(status_data, status_json)

        self.run_coverage()

        # All the files have been reported again.
        self.assert_exists("htmlcov/index.html")
        self.assert_exists("htmlcov/helper1_py.html")
        self.assert_exists("htmlcov/main_file_py.html")
        self.assert_exists("htmlcov/helper2_py.html")


class HtmlTitleTest(HtmlTestHelpers, CoverageTest):
    """Tests of the HTML title support."""

    def test_default_title(self):
        self.create_initial_files()
        self.run_coverage()
        index = self.get_html_index_content()
        self.assertIn("<title>Coverage report</title>", index)
        self.assertIn("<h1>Coverage report:", index)

    def test_title_set_in_config_file(self):
        self.create_initial_files()
        self.make_file(".coveragerc", "[html]\ntitle = Metrics & stuff!\n")
        self.run_coverage()
        index = self.get_html_index_content()
        self.assertIn("<title>Metrics &amp; stuff!</title>", index)
        self.assertIn("<h1>Metrics &amp; stuff!:", index)

    def test_non_ascii_title_set_in_config_file(self):
        self.create_initial_files()
        self.make_file(".coveragerc", "[html]\ntitle = «ταБЬℓσ» numbers")
        self.run_coverage()
        index = self.get_html_index_content()
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
        index = self.get_html_index_content()
        self.assertIn(
            "<title>&#171;&#964;&#945;&#1041;&#1068;&#8467;&#963;&#187;"
            " &amp; st&#252;ff!</title>", index
        )
        self.assertIn(
            "<h1>&#171;&#964;&#945;&#1041;&#1068;&#8467;&#963;&#187;"
            " &amp; st&#252;ff!:", index
        )


class HtmlWithUnparsableFilesTest(HtmlTestHelpers, CoverageTest):
    """Test the behavior when measuring unparsable files."""

    def test_dotpy_not_python(self):
        self.make_file("innocuous.py", "a = 1")
        cov = coverage.Coverage()
        self.start_import_stop(cov, "innocuous")
        self.make_file("innocuous.py", "<h1>This isn't python!</h1>")
        msg = "Couldn't parse '.*innocuous.py' as Python source: .* at line 1"
        with self.assertRaisesRegex(NotPython, msg):
            cov.html_report()

    def test_dotpy_not_python_ignored(self):
        self.make_file("innocuous.py", "a = 2")
        cov = coverage.Coverage()
        self.start_import_stop(cov, "innocuous")
        self.make_file("innocuous.py", "<h1>This isn't python!</h1>")
        cov.html_report(ignore_errors=True)
        self.assertEqual(
            len(cov._warnings),
            1,
            "Expected a warning to be thrown when an invalid python file is parsed")
        self.assertIn(
            "Could not parse Python file",
            cov._warnings[0],
            "Warning message should be in 'invalid file' warning"
        )
        self.assertIn(
            "innocuous.py",
            cov._warnings[0],
            "Filename should be in 'invalid file' warning"
        )
        self.assert_exists("htmlcov/index.html")
        # This would be better as a glob, if the HTML layout changes:
        self.assert_doesnt_exist("htmlcov/innocuous.html")

    def test_dothtml_not_python(self):
        # We run a .html file, and when reporting, we can't parse it as
        # Python.  Since it wasn't .py, no error is reported.

        # Run an "HTML" file
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
        source = "exec(compile('','','exec'), {'__file__': 'liar.html'})"
        self.make_file("liar.py", source)
        self.make_file("liar.html", "{# Whoops, not python code #}")
        cov = coverage.Coverage()
        self.start_import_stop(cov, "liar")
        cov.html_report()
        self.assert_exists("htmlcov/index.html")

    def test_execed_liar_ignored_indentation_error(self):
        # Jinja2 sets __file__ to be a non-Python file, and then execs code.
        # If that file contains untokenizable code, we shouldn't get an
        # exception.
        source = "exec(compile('','','exec'), {'__file__': 'liar.html'})"
        self.make_file("liar.py", source)
        # Tokenize will raise an IndentationError if it can't dedent.
        self.make_file("liar.html", "0\n  2\n 1\n")
        cov = coverage.Coverage()
        self.start_import_stop(cov, "liar")
        cov.html_report()
        self.assert_exists("htmlcov/index.html")

    def test_decode_error(self):
        # https://bitbucket.org/ned/coveragepy/issue/351/files-with-incorrect-encoding-are-ignored
        # imp.load_module won't load a file with an undecodable character
        # in a comment, though Python will run them.  So we'll change the
        # file after running.
        self.make_file("main.py", "import sub.not_ascii")
        self.make_file("sub/__init__.py")
        self.make_file("sub/not_ascii.py", """\
            # coding: utf8
            a = 1  # Isn't this great?!
            """)
        cov = coverage.Coverage()
        self.start_import_stop(cov, "main")

        # Create the undecodable version of the file. make_file is too helpful,
        # so get down and dirty with bytes.
        with open("sub/not_ascii.py", "wb") as f:
            f.write(b"# coding: utf8\na = 1  # Isn't this great?\xcb!\n")

        with open("sub/not_ascii.py", "rb") as f:
            undecodable = f.read()
        self.assertIn(b"?\xcb!", undecodable)

        cov.html_report()

        html_report = self.get_html_report_content("sub/not_ascii.py")
        expected = "# Isn't this great?&#65533;!"
        self.assertIn(expected, html_report)

    def test_formfeeds(self):
        # https://bitbucket.org/ned/coveragepy/issue/360/html-reports-get-confused-by-l-in-the-code
        self.make_file("formfeed.py", "line_one = 1\n\f\nline_two = 2\n")
        cov = coverage.Coverage()
        self.start_import_stop(cov, "formfeed")
        cov.html_report()

        formfeed_html = self.get_html_report_content("formfeed.py")
        self.assertIn("line_two", formfeed_html)


class HtmlTest(HtmlTestHelpers, CoverageTest):
    """Moar HTML tests."""

    def test_missing_source_file_incorrect_message(self):
        # https://bitbucket.org/ned/coveragepy/issue/60
        self.make_file("thefile.py", "import sub.another\n")
        self.make_file("sub/__init__.py", "")
        self.make_file("sub/another.py", "print('another')\n")
        cov = coverage.Coverage()
        self.start_import_stop(cov, 'thefile')
        os.remove("sub/another.py")

        missing_file = os.path.join(self.temp_dir, "sub", "another.py")
        missing_file = os.path.realpath(missing_file)
        msg = "(?i)No source for code: '%s'" % re.escape(missing_file)
        with self.assertRaisesRegex(NoSource, msg):
            cov.html_report()

    def test_extensionless_file_collides_with_extension(self):
        # It used to be that "program" and "program.py" would both be reported
        # to "program.html".  Now they are not.
        # https://bitbucket.org/ned/coveragepy/issue/69
        self.make_file("program", "import program\n")
        self.make_file("program.py", "a = 1\n")
        self.run_command("coverage run program")
        self.run_command("coverage html")
        self.assert_exists("htmlcov/index.html")
        self.assert_exists("htmlcov/program.html")
        self.assert_exists("htmlcov/program_py.html")

    def test_has_date_stamp_in_files(self):
        self.create_initial_files()
        self.run_coverage()

        with open("htmlcov/index.html") as f:
            self.assert_correct_timestamp(f.read())
        with open("htmlcov/main_file_py.html") as f:
            self.assert_correct_timestamp(f.read())

    def test_reporting_on_unmeasured_file(self):
        # It should be ok to ask for an HTML report on a file that wasn't even
        # measured at all.  https://bitbucket.org/ned/coveragepy/issues/403
        self.create_initial_files()
        self.make_file("other.py", "a = 1\n")
        self.run_coverage(htmlargs=dict(morfs=['other.py']))
        self.assert_exists("htmlcov/index.html")
        self.assert_exists("htmlcov/other_py.html")

    def test_shining_panda_fix(self):
        # The ShiningPanda plugin looks for "status.dat" to find HTML reports.
        # Accommodate them, but only if we are running under Jenkins.
        self.set_environ("JENKINS_URL", "Something or other")
        self.create_initial_files()
        self.run_coverage()
        self.assert_exists("htmlcov/status.dat")

    def test_report_skip_covered_no_branches(self):
        self.make_file("main_file.py", """
            import not_covered

            def normal():
                print("z")
            normal()
        """)
        self.make_file("not_covered.py", """
            def not_covered():
                print("n")
        """)
        self.run_coverage(htmlargs=dict(skip_covered=True))
        self.assert_exists("htmlcov/index.html")
        self.assert_doesnt_exist("htmlcov/main_file_py.html")
        self.assert_exists("htmlcov/not_covered_py.html")

    def test_report_skip_covered_branches(self):
        self.make_file("main_file.py", """
            import not_covered

            def normal():
                print("z")
            normal()
        """)
        self.make_file("not_covered.py", """
            def not_covered():
                print("n")
        """)
        self.run_coverage(covargs=dict(branch=True), htmlargs=dict(skip_covered=True))
        self.assert_exists("htmlcov/index.html")
        self.assert_doesnt_exist("htmlcov/main_file_py.html")
        self.assert_exists("htmlcov/not_covered_py.html")


class HtmlStaticFileTest(CoverageTest):
    """Tests of the static file copying for the HTML report."""

    def setUp(self):
        super(HtmlStaticFileTest, self).setUp()
        self.original_path = list(coverage.html.STATIC_PATH)
        self.addCleanup(self.cleanup_static_path)

    def cleanup_static_path(self):
        """A cleanup."""
        coverage.html.STATIC_PATH = self.original_path

    def test_copying_static_files_from_system(self):
        # Make a new place for static files.
        self.make_file("static_here/jquery.min.js", "Not Really JQuery!")
        coverage.html.STATIC_PATH.insert(0, "static_here")

        self.make_file("main.py", "print(17)")
        cov = coverage.Coverage()
        self.start_import_stop(cov, "main")
        cov.html_report()

        with open("htmlcov/jquery.min.js") as f:
            jquery = f.read()
        self.assertEqual(jquery, "Not Really JQuery!")

    def test_copying_static_files_from_system_in_dir(self):
        # Make a new place for static files.
        INSTALLED = [
            "jquery/jquery.min.js",
            "jquery-hotkeys/jquery.hotkeys.js",
            "jquery-isonscreen/jquery.isonscreen.js",
            "jquery-tablesorter/jquery.tablesorter.min.js",
        ]
        for fpath in INSTALLED:
            self.make_file(os.path.join("static_here", fpath), "Not real.")
        coverage.html.STATIC_PATH.insert(0, "static_here")

        self.make_file("main.py", "print(17)")
        cov = coverage.Coverage()
        self.start_import_stop(cov, "main")
        cov.html_report()

        for fpath in INSTALLED:
            the_file = os.path.basename(fpath)
            with open(os.path.join("htmlcov", the_file)) as f:
                contents = f.read()
            self.assertEqual(contents, "Not real.")

    def test_cant_find_static_files(self):
        # Make the path point to useless places.
        coverage.html.STATIC_PATH = ["/xyzzy"]

        self.make_file("main.py", "print(17)")
        cov = coverage.Coverage()
        self.start_import_stop(cov, "main")
        msg = "Couldn't find static file u?'.*'"
        with self.assertRaisesRegex(CoverageException, msg):
            cov.html_report()


class HtmlGoldTests(CoverageGoldTest):
    """Tests of HTML reporting that use gold files."""

    root_dir = 'tests/farm/html'

    def test_a(self):
        self.output_dir("out/a")

        with change_dir("src"):
            # pylint: disable=import-error
            cov = coverage.Coverage()
            cov.start()
            import a            # pragma: nested
            cov.stop()          # pragma: nested
            cov.html_report(a, directory='../out/a')

        compare("gold_a", "out/a", size_within=10, file_pattern="*.html")
        contains(
            "out/a/a_py.html",
            ('<span class="key">if</span> <span class="num">1</span> '
             '<span class="op">&lt;</span> <span class="num">2</span>'),
            ('    <span class="nam">a</span> '
             '<span class="op">=</span> <span class="num">3</span>'),
            '<span class="pc_cov">67%</span>',
        )
        contains(
            "out/a/index.html",
            '<a href="a_py.html">a.py</a>',
            '<span class="pc_cov">67%</span>',
            '<td class="right" data-ratio="2 3">67%</td>',
        )

    def test_b_branch(self):
        self.output_dir("out/b_branch")

        with change_dir("src"):
            # pylint: disable=import-error
            cov = coverage.Coverage(branch=True)
            cov.start()
            import b            # pragma: nested
            cov.stop()          # pragma: nested
            cov.html_report(b, directory="../out/b_branch")

        compare("gold_b_branch", "out/b_branch", size_within=10, file_pattern="*.html")
        contains(
            "out/b_branch/b_py.html",
            ('<span class="key">if</span> <span class="nam">x</span> '
             '<span class="op">&lt;</span> <span class="num">2</span>'),
            ('    <span class="nam">a</span> <span class="op">=</span> '
             '<span class="num">3</span>'),
            '<span class="pc_cov">70%</span>',
            ('<span class="annotate short">8&#x202F;&#x219B;&#x202F;11</span>'
             '<span class="annotate long">line 8 didn\'t jump to line 11, '
                            'because the condition on line 8 was never false</span>'),
            ('<span class="annotate short">17&#x202F;&#x219B;&#x202F;exit</span>'
             '<span class="annotate long">line 17 didn\'t return from function \'two\', '
                            'because the condition on line 17 was never false</span>'),
            ('<span class="annotate short">25&#x202F;&#x219B;&#x202F;26,&nbsp;&nbsp; '
                            '25&#x202F;&#x219B;&#x202F;28</span>'
             '<span class="annotate long">2 missed branches: '
                            '1) line 25 didn\'t jump to line 26, '
                                'because the condition on line 25 was never true, '
                            '2) line 25 didn\'t jump to line 28, '
                                'because the condition on line 25 was never false</span>'),
        )
        contains(
            "out/b_branch/index.html",
            '<a href="b_py.html">b.py</a>',
            '<span class="pc_cov">70%</span>',
            '<td class="right" data-ratio="16 23">70%</td>',
        )

    def test_bom(self):
        self.output_dir("out/bom")

        with change_dir("src"):
            # pylint: disable=import-error
            cov = coverage.Coverage()
            cov.start()
            import bom          # pragma: nested
            cov.stop()          # pragma: nested
            cov.html_report(bom, directory="../out/bom")

        compare("gold_bom", "out/bom", size_within=10, file_pattern="*.html")
        contains(
            "out/bom/bom_py.html",
            '<span class="str">"3&#215;4 = 12, &#247;2 = 6&#177;0"</span>',
        )

    def test_isolatin1(self):
        self.output_dir("out/isolatin1")

        with change_dir("src"):
            # pylint: disable=import-error
            cov = coverage.Coverage()
            cov.start()
            import isolatin1            # pragma: nested
            cov.stop()                  # pragma: nested
            cov.html_report(isolatin1, directory="../out/isolatin1")

        compare("gold_isolatin1", "out/isolatin1", size_within=10, file_pattern="*.html")
        contains(
            "out/isolatin1/isolatin1_py.html",
            '<span class="str">"3&#215;4 = 12, &#247;2 = 6&#177;0"</span>',
        )

    def test_omit_1(self):
        self.output_dir("out/omit_1")

        with change_dir("src"):
            # pylint: disable=import-error
            cov = coverage.Coverage(include=["./*"])
            cov.start()
            import main         # pragma: nested # pylint: disable=unused-variable
            cov.stop()          # pragma: nested
            cov.html_report(directory="../out/omit_1")

        compare("gold_omit_1", "out/omit_1", size_within=10, file_pattern="*.html")

    def test_omit_2(self):
        self.output_dir("out/omit_2")

        with change_dir("src"):
            # pylint: disable=import-error
            cov = coverage.Coverage(include=["./*"])
            cov.start()
            import main         # pragma: nested # pylint: disable=unused-variable
            cov.stop()          # pragma: nested
            cov.html_report(directory="../out/omit_2", omit=["m1.py"])

        compare("gold_omit_2", "out/omit_2", size_within=10, file_pattern="*.html")

    def test_omit_3(self):
        self.output_dir("out/omit_3")

        with change_dir("src"):
            # pylint: disable=import-error
            cov = coverage.Coverage(include=["./*"])
            cov.start()
            import main         # pragma: nested # pylint: disable=unused-variable
            cov.stop()          # pragma: nested
            cov.html_report(directory="../out/omit_3", omit=["m1.py", "m2.py"])

        compare("gold_omit_3", "out/omit_3", size_within=10, file_pattern="*.html")

    def test_omit_4(self):
        self.output_dir("out/omit_4")

        with change_dir("src"):
            # pylint: disable=import-error
            cov = coverage.Coverage(config_file="omit4.ini", include=["./*"])
            cov.start()
            import main         # pragma: nested # pylint: disable=unused-variable
            cov.stop()          # pragma: nested
            cov.html_report(directory="../out/omit_4")

        compare("gold_omit_4", "out/omit_4", size_within=10, file_pattern="*.html")

    def test_omit_5(self):
        self.output_dir("out/omit_5")

        with change_dir("src"):
            # pylint: disable=import-error
            cov = coverage.Coverage(config_file="omit5.ini", include=["./*"])
            cov.start()
            import main         # pragma: nested # pylint: disable=unused-variable
            cov.stop()          # pragma: nested
            cov.html_report()

        compare("gold_omit_5", "out/omit_5", size_within=10, file_pattern="*.html")

    def test_other(self):
        self.output_dir("out/other")

        with change_dir("src"):
            # pylint: disable=import-error
            sys.path.insert(0, "../othersrc")
            cov = coverage.Coverage(include=["./*", "../othersrc/*"])
            cov.start()
            import here         # pragma: nested # pylint: disable=unused-variable
            cov.stop()          # pragma: nested
            cov.html_report(directory="../out/other")

        # Different platforms will name the "other" file differently. Rename it
        for p in glob.glob("out/other/*_other_py.html"):
            os.rename(p, "out/other/blah_blah_other_py.html")

        compare("gold_other", "out/other", size_within=10, file_pattern="*.html")
        contains(
            "out/other/index.html",
            '<a href="here_py.html">here.py</a>',
            'other_py.html">', 'other.py</a>',
        )

    def test_partial(self):
        self.output_dir("out/partial")

        with change_dir("src"):
            # pylint: disable=import-error
            cov = coverage.Coverage(config_file="partial.ini")
            cov.start()
            import partial          # pragma: nested
            cov.stop()              # pragma: nested
            cov.html_report(partial, directory="../out/partial")

        compare("gold_partial", "out/partial", size_within=10, file_pattern="*.html")
        contains(
            "out/partial/partial_py.html",
            '<p id="t8" class="stm run hide_run">',
            '<p id="t11" class="stm run hide_run">',
            '<p id="t14" class="stm run hide_run">',
            # The "if 0" and "if 1" statements are optimized away.
            '<p id="t17" class="pln">',
            # The "raise AssertionError" is excluded by regex in the .ini.
            '<p id="t24" class="exc">',
        )
        contains(
            "out/partial/index.html",
            '<a href="partial_py.html">partial.py</a>',
        )
        contains(
            "out/partial/index.html",
            '<span class="pc_cov">100%</span>'
        )

    def test_styled(self):
        self.output_dir("out/styled")

        with change_dir("src"):
            # pylint: disable=import-error
            cov = coverage.Coverage()
            cov.start()
            import a            # pragma: nested
            cov.stop()          # pragma: nested
            cov.html_report(a, directory="../out/styled", extra_css="extra.css")

        compare("gold_styled", "out/styled", size_within=10, file_pattern="*.html")
        compare("gold_styled", "out/styled", size_within=10, file_pattern="*.css")
        contains(
            "out/styled/a_py.html",
            '<link rel="stylesheet" href="extra.css" type="text/css">',
            ('<span class="key">if</span> <span class="num">1</span> '
             '<span class="op">&lt;</span> <span class="num">2</span>'),
            ('    <span class="nam">a</span> <span class="op">=</span> '
             '<span class="num">3</span>'),
            '<span class="pc_cov">67%</span>'
        )
        contains(
            "out/styled/index.html",
            '<link rel="stylesheet" href="extra.css" type="text/css">',
            '<a href="a_py.html">a.py</a>',
            '<span class="pc_cov">67%</span>'
        )

    def test_tabbed(self):
        self.output_dir("out/tabbed")

        with change_dir("src"):
            # pylint: disable=import-error
            cov = coverage.Coverage()
            cov.start()
            import tabbed           # pragma: nested
            cov.stop()              # pragma: nested
            cov.html_report(tabbed, directory="../out/tabbed")

        # Editors like to change things, make sure our source file still has tabs.
        contains("src/tabbed.py", "\tif x:\t\t\t\t\t# look nice")

        contains(
            "out/tabbed/tabbed_py.html",
            '>        <span class="key">if</span> '
            '<span class="nam">x</span><span class="op">:</span>'
            '                                   '
            '<span class="com"># look nice</span>'
        )

        doesnt_contain("out/tabbed/tabbed_py.html", "\t")

    def test_unicode(self):
        self.output_dir("out/unicode")

        with change_dir("src"):
            # pylint: disable=import-error, redefined-builtin
            cov = coverage.Coverage()
            cov.start()
            import unicode          # pragma: nested
            cov.stop()              # pragma: nested
            cov.html_report(unicode, directory="../out/unicode")

        compare("gold_unicode", "out/unicode", size_within=10, file_pattern="*.html")
        contains(
            "out/unicode/unicode_py.html",
            '<span class="str">"&#654;d&#729;&#477;b&#592;&#633;&#477;&#652;o&#596;"</span>',
        )

        contains_any(
            "out/unicode/unicode_py.html",
            '<span class="str">"db40,dd00: x&#56128;&#56576;"</span>',
            '<span class="str">"db40,dd00: x&#917760;"</span>',
        )
