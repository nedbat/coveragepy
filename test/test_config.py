"""Test the config file handling for coverage.py"""

import os, sys
import coverage

sys.path.insert(0, os.path.split(__file__)[0]) # Force relative import for Py3k
from coveragetest import CoverageTest


class ConfigTest(CoverageTest):
    """Tests of the different sources of configuration settings."""

    def test_default_config(self):
        # Just constructing a coverage() object gets the right defaults.
        cov = coverage.coverage()
        self.assertFalse(cov.config.timid)
        self.assertFalse(cov.config.branch)
        self.assertEqual(cov.config.data_file, ".coverage")

    def test_arguments(self):
        # Arguments to the constructor are applied to the configuation.
        cov = coverage.coverage(timid=True, data_file="fooey.dat")
        self.assertTrue(cov.config.timid)
        self.assertFalse(cov.config.branch)
        self.assertEqual(cov.config.data_file, "fooey.dat")

    def test_config_file(self):
        # A .coveragerc file will be read into the configuration.
        self.make_file(".coveragerc", """\
            # This is just a bogus .rc file for testing.
            [run]
            timid =         True
            data_file =     .hello_kitty.data
            """)
        cov = coverage.coverage()
        self.assertTrue(cov.config.timid)
        self.assertFalse(cov.config.branch)
        self.assertEqual(cov.config.data_file, ".hello_kitty.data")

    def test_named_config_file(self):
        # You can name the config file what you like.
        self.make_file("my_cov.ini", """\
            [run]
            timid = True
            ; I wouldn't really use this as a data file...
            data_file = delete.me
            """)
        cov = coverage.coverage(config_file="my_cov.ini")
        self.assertTrue(cov.config.timid)
        self.assertFalse(cov.config.branch)
        self.assertEqual(cov.config.data_file, "delete.me")

    def test_ignored_config_file(self):
        # You can disable reading the .coveragerc file.
        self.make_file(".coveragerc", """\
            [run]
            timid = True
            data_file = delete.me
            """)
        cov = coverage.coverage(config_file=False)
        self.assertFalse(cov.config.timid)
        self.assertFalse(cov.config.branch)
        self.assertEqual(cov.config.data_file, ".coverage")

    def test_config_file_then_args(self):
        # The arguments override the .coveragerc file.
        self.make_file(".coveragerc", """\
            [run]
            timid = True
            data_file = weirdo.file
            """)
        cov = coverage.coverage(timid=False, data_file=".mycov")
        self.assertFalse(cov.config.timid)
        self.assertFalse(cov.config.branch)
        self.assertEqual(cov.config.data_file, ".mycov")

    def test_data_file_from_environment(self):
        # There's an environment variable for the data_file.
        self.make_file(".coveragerc", """\
            [run]
            timid = True
            data_file = weirdo.file
            """)
        self.set_environ("COVERAGE_FILE", "fromenv.dat")
        cov = coverage.coverage()
        self.assertEqual(cov.config.data_file, "fromenv.dat")
        # But the constructor args override the env var.
        cov = coverage.coverage(data_file="fromarg.dat")
        self.assertEqual(cov.config.data_file, "fromarg.dat")


class ConfigFileTest(CoverageTest):
    """Tests of the config file settings in particular."""

    def test_config_file_settings(self):
        # This sample file tries to use lots of variation of syntax...
        self.make_file(".coveragerc", """\
            # This is a settings file for coverage.py
            [run]
            timid = yes
            data_file = something_or_other.dat
            branch = 1
            cover_pylib = TRUE
            parallel = on

            [report]
            ; these settings affect reporting.
            exclude_lines =
                if 0:

                pragma:?\\s+no cover
                    another_tab

            ignore_errors = TRUE
            omit =
                one, another, some_more,
                    yet_more

            [html]

            directory    =     c:\\tricky\\dir.somewhere

            [xml]
            output=mycov.xml

            """)
        cov = coverage.coverage()

        self.assertTrue(cov.config.timid)
        self.assertEqual(cov.config.data_file, "something_or_other.dat")
        self.assertTrue(cov.config.branch)
        self.assertTrue(cov.config.cover_pylib)
        self.assertTrue(cov.config.parallel)

        self.assertEqual(cov.get_exclude_list(),
            ["if 0:", "pragma:?\s+no cover", "another_tab"]
            )
        self.assertTrue(cov.config.ignore_errors)
        self.assertEqual(cov.config.omit_prefixes,
            ["one", "another", "some_more", "yet_more"]
            )

        self.assertEqual(cov.config.html_dir, r"c:\tricky\dir.somewhere")

        self.assertEqual(cov.config.xml_output, "mycov.xml")
