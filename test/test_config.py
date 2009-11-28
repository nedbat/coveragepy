"""Test the config file handling for coverage.py"""

import os, sys
import coverage

sys.path.insert(0, os.path.split(__file__)[0]) # Force relative import for Py3k
from coveragetest import CoverageTest


class ConfigTest(CoverageTest):
    """Tests of the config file support."""

    def test_default_config(self):
        # Just constructing a coverage() object gets the right defaults.
        cov = coverage.coverage()
        self.assertFalse(cov.config.timid)
        self.assertFalse(cov.config.branch)

    def test_arguments(self):
        # Arguments to the constructor are applied to the configuation.
        cov = coverage.coverage(timid=True)
        self.assert_(cov.config.timid)
        self.assertFalse(cov.config.branch)

    def test_config_file(self):
        # A .coveragerc file will be read into the configuration.
        self.make_file(".coveragerc", """\
            [run]
            timid = True
            """)
        cov = coverage.coverage()
        self.assert_(cov.config.timid)
        self.assertFalse(cov.config.branch)

    def test_named_config_file(self):
        # You can name the config file what you like.
        self.make_file("my_cov.ini", """\
            [run]
            timid = True
            """)
        cov = coverage.coverage(config_file="my_cov.ini")
        self.assert_(cov.config.timid)
        self.assertFalse(cov.config.branch)

    def test_ignored_config_file(self):
        # You can disable reading the .coveragerc file.
        self.make_file(".coveragerc", """\
            [run]
            timid = True
            """)
        cov = coverage.coverage(config_file=False)
        self.assertFalse(cov.config.timid)
        self.assertFalse(cov.config.branch)

    def test_config_file_then_args(self):
        # The arguments override the .coveragerc file.
        self.make_file(".coveragerc", """\
            [run]
            timid = True
            """)
        cov = coverage.coverage(timid=False)
        self.assertFalse(cov.config.timid)
        self.assertFalse(cov.config.branch)
