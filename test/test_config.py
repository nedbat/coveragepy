# -*- coding: utf-8 -*-
"""Test the config file handling for coverage.py"""

import sys
import coverage
from coverage.misc import CoverageException

from test.coveragetest import CoverageTest


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

    def test_parse_errors(self):
        # Im-parseable values raise CoverageException
        self.make_file(".coveragerc", """\
            [run]
            timid = maybe?
            """)
        self.assertRaises(CoverageException, coverage.coverage)

    def test_environment_vars_in_config(self):
        # Config files can have $envvars in them.
        self.make_file(".coveragerc", """\
            [run]
            data_file = $DATA_FILE.fooey
            branch = $OKAY
            [report]
            exclude_lines =
                the_$$one
                another${THING}
                x${THING}y
                x${NOTHING}y
                huh$${X}what
            """)
        self.set_environ("DATA_FILE", "hello-world")
        self.set_environ("THING", "ZZZ")
        self.set_environ("OKAY", "yes")
        cov = coverage.coverage()
        self.assertEqual(cov.config.data_file, "hello-world.fooey")
        self.assertEqual(cov.config.branch, True)
        self.assertEqual(cov.config.exclude_list,
            ["the_$one", "anotherZZZ", "xZZZy", "xy", "huh${X}what"]
            )


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
            include = a/   ,    b/

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
            precision = 3

            partial_branches =
                pragma:?\\s+no branch
            partial_branches_always =
                if 0:
                while True:

            show_missing= TruE

            [html]

            directory    =     c:\\tricky\\dir.somewhere
            extra_css=something/extra.css
            title = Title & nums # nums!
            [xml]
            output=mycov.xml

            [paths]
            source =
                .
                /home/ned/src/

            other = other, /home/ned/other, c:\\Ned\\etc

            """)
        cov = coverage.coverage()

        self.assertTrue(cov.config.timid)
        self.assertEqual(cov.config.data_file, "something_or_other.dat")
        self.assertTrue(cov.config.branch)
        self.assertTrue(cov.config.cover_pylib)
        self.assertTrue(cov.config.parallel)

        self.assertEqual(cov.get_exclude_list(),
            ["if 0:", r"pragma:?\s+no cover", "another_tab"]
            )
        self.assertTrue(cov.config.ignore_errors)
        self.assertEqual(cov.config.include, ["a/", "b/"])
        self.assertEqual(cov.config.omit,
            ["one", "another", "some_more", "yet_more"]
            )
        self.assertEqual(cov.config.precision, 3)

        self.assertEqual(cov.config.partial_list,
            [r"pragma:?\s+no branch"]
            )
        self.assertEqual(cov.config.partial_always_list,
            ["if 0:", "while True:"]
            )
        self.assertTrue(cov.config.show_missing)
        self.assertEqual(cov.config.html_dir, r"c:\tricky\dir.somewhere")
        self.assertEqual(cov.config.extra_css, "something/extra.css")
        self.assertEqual(cov.config.html_title, "Title & nums # nums!")

        self.assertEqual(cov.config.xml_output, "mycov.xml")

        self.assertEqual(cov.config.paths, {
            'source': ['.', '/home/ned/src/'],
            'other': ['other', '/home/ned/other', 'c:\\Ned\\etc']
            })

    if sys.version_info[:2] != (3,1):
        def test_one(self):
            # This sample file tries to use lots of variation of syntax...
            self.make_file(".coveragerc", """\
                [html]
                title = tabblo & «ταБЬℓσ» # numbers
                """)
            cov = coverage.coverage()

            self.assertEqual(cov.config.html_title,
                "tabblo & «ταБЬℓσ» # numbers"
                )
