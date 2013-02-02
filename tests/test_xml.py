"""Tests for XML reports from coverage.py."""

import os, re
import coverage

from tests.coveragetest import CoverageTest

class XmlReportTest(CoverageTest):
    """Tests of the XML reports from coverage.py."""

    def run_mycode(self):
        """Run mycode.py, so we can report on it."""
        self.make_file("mycode.py", "print('hello')\n")
        self.run_command("coverage run mycode.py")

    def test_default_file_placement(self):
        self.run_mycode()
        self.run_command("coverage xml")
        self.assert_exists("coverage.xml")

    def test_argument_affects_xml_placement(self):
        self.run_mycode()
        self.run_command("coverage xml -o put_it_there.xml")
        self.assert_doesnt_exist("coverage.xml")
        self.assert_exists("put_it_there.xml")

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

    def run_doit(self):
        """Construct a simple sub-package."""
        self.make_file("sub/__init__.py")
        self.make_file("sub/doit.py", "print('doit!')")
        self.make_file("main.py", "import sub.doit")
        cov = coverage.coverage()
        self.start_import_stop(cov, "main")
        return cov

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
        import sub.doit                         # pylint: disable=F0401
        cov.xml_report([sub.doit], outfile="-")
        xml = self.stdout()
        doit_line = re_line(xml, "class.*doit")
        self.assertIn('filename="sub/doit.py"', doit_line)


def re_line(text, pat):
    """Return the one line in `text` that matches regex `pat`."""
    lines = [l for l in text.splitlines() if re.search(pat, l)]
    return lines[0]
