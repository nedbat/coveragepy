"""Tests for XML reports from coverage.py."""

import os, sys

sys.path.insert(0, os.path.split(__file__)[0]) # Force relative import for Py3k
from coveragetest import CoverageTest

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
        self.run_command("coverage xml")
        self.assert_doesnt_exist("coverage.xml")
