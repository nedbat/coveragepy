"""Tests for XML reports from coverage.py."""

import os
import re

import coverage

from tests.coveragetest import CoverageTest


class XmlTestHelpers(CoverageTest):
    """Methods to use from XML tests."""

    def run_mycode(self):
        """Run mycode.py, so we can report on it."""
        self.make_file("mycode.py", "print('hello')\n")
        self.run_command("coverage run mycode.py")

    def run_doit(self):
        """Construct a simple sub-package."""
        self.make_file("sub/__init__.py")
        self.make_file("sub/doit.py", "print('doit!')")
        self.make_file("main.py", "import sub.doit")
        cov = coverage.coverage()
        self.start_import_stop(cov, "main")
        return cov

    def make_tree(self, width, depth, curdir="."):
        """Make a tree of packages.

        Makes `width` directories, named d0 .. d{width-1}. Each directory has
        __init__.py, and `width` files, named f0.py .. f{width-1}.py.  Each
        directory also has `width` subdirectories, in the same fashion, until
        a depth of `depth` is reached.

        """
        if depth == 0:
            return

        def here(p):
            """A path for `p` in our currently interesting directory."""
            return os.path.join(curdir, p)

        for i in range(width):
            next_dir = here("d{0}".format(i))
            self.make_tree(width, depth-1, next_dir)
        if curdir != ".":
            self.make_file(here("__init__.py"), "")
            for i in range(width):
                filename = here("f{0}.py".format(i))
                self.make_file(filename, "# {0}\n".format(filename))


class XmlReportTest(XmlTestHelpers, CoverageTest):
    """Tests of the XML reports from coverage.py."""

    def test_default_file_placement(self):
        self.run_mycode()
        self.run_command("coverage xml")
        self.assert_exists("coverage.xml")

    def test_argument_affects_xml_placement(self):
        self.run_mycode()
        self.run_command("coverage xml -o put_it_there.xml")
        self.assert_doesnt_exist("coverage.xml")
        self.assert_exists("put_it_there.xml")

    def test_config_file_directory_does_not_exist(self):
        self.run_mycode()
        self.run_command("coverage xml -o nonexistent/put_it_there.xml")
        self.assert_doesnt_exist("coverage.xml")
        self.assert_doesnt_exist("put_it_there.xml")
        self.assert_exists("nonexistent/put_it_there.xml")

    def test_config_affects_xml_placement(self):
        self.run_mycode()
        self.make_file(".coveragerc", "[xml]\noutput = xml.out\n")
        self.run_command("coverage xml")
        self.assert_doesnt_exist("coverage.xml")
        self.assert_exists("xml.out")

    def test_no_data(self):
        # https://bitbucket.org/ned/coveragepy/issue/210
        self.run_command("coverage xml")
        self.assert_doesnt_exist("coverage.xml")

    def test_no_source(self):
        # Written while investigating a bug, might as well keep it.
        # https://bitbucket.org/ned/coveragepy/issue/208
        self.make_file("innocuous.py", "a = 4")
        cov = coverage.coverage()
        self.start_import_stop(cov, "innocuous")
        os.remove("innocuous.py")
        cov.xml_report(ignore_errors=True)
        self.assert_exists("coverage.xml")

    def test_filename_format_showing_everything(self):
        cov = self.run_doit()
        cov.xml_report(outfile="-")
        xml = self.stdout()
        doit_line = re_line(xml, "class.*doit")
        self.assertIn('filename="sub/doit.py"', doit_line)

    def test_filename_format_including_filename(self):
        cov = self.run_doit()
        cov.xml_report(["sub/doit.py"], outfile="-")
        xml = self.stdout()
        doit_line = re_line(xml, "class.*doit")
        self.assertIn('filename="sub/doit.py"', doit_line)

    def test_filename_format_including_module(self):
        cov = self.run_doit()
        import sub.doit                         # pylint: disable=import-error
        cov.xml_report([sub.doit], outfile="-")
        xml = self.stdout()
        doit_line = re_line(xml, "class.*doit")
        self.assertIn('filename="sub/doit.py"', doit_line)

    def test_reporting_on_nothing(self):
        # Used to raise a zero division error:
        # https://bitbucket.org/ned/coveragepy/issue/250
        self.make_file("empty.py", "")
        cov = coverage.coverage()
        empty = self.start_import_stop(cov, "empty")
        cov.xml_report([empty], outfile="-")
        xml = self.stdout()
        empty_line = re_line(xml, "class.*empty")
        self.assertIn('filename="empty.py"', empty_line)
        self.assertIn('line-rate="1"', empty_line)

    def test_empty_file_is_100_not_0(self):
        # https://bitbucket.org/ned/coveragepy/issue/345
        cov = self.run_doit()
        cov.xml_report(outfile="-")
        xml = self.stdout()
        init_line = re_line(xml, 'filename="sub/__init__.py"')
        self.assertIn('line-rate="1"', init_line)


class XmlPackageStructureTest(XmlTestHelpers, CoverageTest):
    """Tests about the package structure reported in the coverage.xml file."""

    def package_and_class_tags(self, cov):
        """Run an XML report on `cov`, and get the package and class tags."""
        self.captured_stdout.truncate(0)
        cov.xml_report(outfile="-")
        packages_and_classes = re_lines(self.stdout(), r"<package |<class ")
        scrubs = r' branch-rate="0"| complexity="0"| line-rate="[\d.]+"'
        return clean("".join(packages_and_classes), scrubs)

    def assert_package_and_class_tags(self, cov, result):
        """Check the XML package and class tags from `cov` match `result`."""
        self.assertMultiLineEqual(
            self.package_and_class_tags(cov),
            clean(result)
            )

    def test_package_names(self):
        self.make_tree(width=1, depth=3)
        self.make_file("main.py", """\
            from d0.d0 import f0
            """)
        cov = coverage.coverage(source=".")
        self.start_import_stop(cov, "main")
        self.assert_package_and_class_tags(cov, """\
            <package name=".">
               <class filename="main.py" name="main.py">
            <package name="d0">
               <class filename="d0/__init__.py" name="__init__.py">
               <class filename="d0/f0.py" name="f0.py">
            <package name="d0.d0">
               <class filename="d0/d0/__init__.py" name="__init__.py">
               <class filename="d0/d0/f0.py" name="f0.py">
            """)

    def test_package_depth(self):
        self.make_tree(width=1, depth=4)
        self.make_file("main.py", """\
            from d0.d0 import f0
            """)
        cov = coverage.coverage(source=".")
        self.start_import_stop(cov, "main")

        cov.config["xml:package_depth"] = 1
        self.assert_package_and_class_tags(cov, """\
            <package name=".">
               <class filename="main.py" name="main.py">
            <package name="d0">
               <class filename="d0/__init__.py" name="__init__.py">
               <class filename="d0/d0/__init__.py" name="d0/__init__.py">
               <class filename="d0/d0/d0/__init__.py" name="d0/d0/__init__.py">
               <class filename="d0/d0/d0/f0.py" name="d0/d0/f0.py">
               <class filename="d0/d0/f0.py" name="d0/f0.py">
               <class filename="d0/f0.py" name="f0.py">
            """)

        cov.config["xml:package_depth"] = 2
        self.assert_package_and_class_tags(cov, """\
            <package name=".">
               <class filename="main.py" name="main.py">
            <package name="d0">
               <class filename="d0/__init__.py" name="__init__.py">
               <class filename="d0/f0.py" name="f0.py">
            <package name="d0.d0">
               <class filename="d0/d0/__init__.py" name="__init__.py">
               <class filename="d0/d0/d0/__init__.py" name="d0/__init__.py">
               <class filename="d0/d0/d0/f0.py" name="d0/f0.py">
               <class filename="d0/d0/f0.py" name="f0.py">
            """)

        cov.config["xml:package_depth"] = 3
        self.assert_package_and_class_tags(cov, """\
            <package name=".">
               <class filename="main.py" name="main.py">
            <package name="d0">
               <class filename="d0/__init__.py" name="__init__.py">
               <class filename="d0/f0.py" name="f0.py">
            <package name="d0.d0">
               <class filename="d0/d0/__init__.py" name="__init__.py">
               <class filename="d0/d0/f0.py" name="f0.py">
            <package name="d0.d0.d0">
               <class filename="d0/d0/d0/__init__.py" name="__init__.py">
               <class filename="d0/d0/d0/f0.py" name="f0.py">
            """)


def re_lines(text, pat):
    """Return a list of lines that match `pat` in the string `text`."""
    lines = [l for l in text.splitlines(True) if re.search(pat, l)]
    return lines


def re_line(text, pat):
    """Return the one line in `text` that matches regex `pat`."""
    lines = re_lines(text, pat)
    assert len(lines) == 1
    return lines[0]


def clean(text, scrub=None):
    """Clean text to prepare it for comparison.

    Remove text matching `scrub`, and leading whitespace. Convert backslashes
    to forward slashes.

    """
    if scrub:
        text = re.sub(scrub, "", text)
    text = re.sub(r"(?m)^\s+", "", text)
    text = re.sub(r"\\", "/", text)
    return text
