# -*- coding: utf-8 -*-
"""Test the config file handling for coverage.py"""

import sys, os

import coverage
from coverage.misc import CoverageException

from tests.coveragetest import CoverageTest


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
        with self.assertRaises(CoverageException):
            coverage.coverage()

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

    def test_tweaks_after_constructor(self):
        # Arguments to the constructor are applied to the configuation.
        cov = coverage.coverage(timid=True, data_file="fooey.dat")
        cov.config["run:timid"] = False

        self.assertFalse(cov.config.timid)
        self.assertFalse(cov.config.branch)
        self.assertEqual(cov.config.data_file, "fooey.dat")

        self.assertFalse(cov.config["run:timid"])
        self.assertFalse(cov.config["run:branch"])
        self.assertEqual(cov.config["run:data_file"], "fooey.dat")

    def test_tweak_error_checking(self):
        # Trying to set an unknown config value raises an error.
        cov = coverage.coverage()
        with self.assertRaises(CoverageException):
            cov.config["run:xyzzy"] = 12
        with self.assertRaises(CoverageException):
            cov.config["xyzzy:foo"] = 12
        with self.assertRaises(CoverageException):
            _ = cov.config["run:xyzzy"]
        with self.assertRaises(CoverageException):
            _ = cov.config["xyzzy:foo"]

    def test_tweak_plugin_options(self):
        # Plugin options have a more flexible syntax.
        cov = coverage.coverage()
        cov.config["run:plugins"] = ["fooey.plugin", "xyzzy.coverage.plugin"]
        cov.config["fooey.plugin:xyzzy"] = 17
        cov.config["xyzzy.coverage.plugin:plugh"] = ["a", "b"]
        with self.assertRaises(CoverageException):
            cov.config["no_such.plugin:foo"] = 23

        self.assertEqual(cov.config["fooey.plugin:xyzzy"], 17)
        self.assertEqual(cov.config["xyzzy.coverage.plugin:plugh"], ["a", "b"])
        with self.assertRaises(CoverageException):
            _ = cov.config["no_such.plugin:foo"]


class ConfigFileTest(CoverageTest):
    """Tests of the config file settings in particular."""

    def setUp(self):
        super(ConfigFileTest, self).setUp()
        # Parent class saves and restores sys.path, we can just modify it.
        # Add modules to the path so we can import plugins.
        sys.path.append(self.nice_file(os.path.dirname(__file__), 'modules'))

    # This sample file tries to use lots of variation of syntax...
    # The {section} placeholder lets us nest these settings in another file.
    LOTSA_SETTINGS = """\
        # This is a settings file for coverage.py
        [{section}run]
        timid = yes
        data_file = something_or_other.dat
        branch = 1
        cover_pylib = TRUE
        parallel = on
        include = a/   ,    b/
        concurrency = thread
        plugins =
            plugins.a_plugin
            plugins.another

        [{section}report]
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
        skip_covered = TruE

        [{section}html]

        directory    =     c:\\tricky\\dir.somewhere
        extra_css=something/extra.css
        title = Title & nums # nums!
        [{section}xml]
        output=mycov.xml

        [{section}paths]
        source =
            .
            /home/ned/src/

        other = other, /home/ned/other, c:\\Ned\\etc

        [{section}plugins.a_plugin]
        hello = world
        ; comments still work.
        names = Jane/John/Jenny
        """

    # Just some sample setup.cfg text from the docs.
    SETUP_CFG = """\
        [bdist_rpm]
        release = 1
        packager = Jane Packager <janep@pysoft.com>
        doc_files = CHANGES.txt
                    README.txt
                    USAGE.txt
                    doc/
                    examples/
        """

    def assert_config_settings_are_correct(self, cov):
        """Check that `cov` has all the settings from LOTSA_SETTINGS."""
        self.assertTrue(cov.config.timid)
        self.assertEqual(cov.config.data_file, "something_or_other.dat")
        self.assertTrue(cov.config.branch)
        self.assertTrue(cov.config.cover_pylib)
        self.assertTrue(cov.config.parallel)
        self.assertEqual(cov.config.concurrency, "thread")

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
        self.assertEqual(cov.config.plugins,
            ["plugins.a_plugin", "plugins.another"]
            )
        self.assertTrue(cov.config.show_missing)
        self.assertTrue(cov.config.skip_covered)
        self.assertEqual(cov.config.html_dir, r"c:\tricky\dir.somewhere")
        self.assertEqual(cov.config.extra_css, "something/extra.css")
        self.assertEqual(cov.config.html_title, "Title & nums # nums!")

        self.assertEqual(cov.config.xml_output, "mycov.xml")

        self.assertEqual(cov.config.paths, {
            'source': ['.', '/home/ned/src/'],
            'other': ['other', '/home/ned/other', 'c:\\Ned\\etc']
            })

        self.assertEqual(cov.config.get_plugin_options("plugins.a_plugin"), {
            'hello': 'world',
            'names': 'Jane/John/Jenny',
            })
        self.assertEqual(cov.config.get_plugin_options("plugins.another"), {})

    def test_config_file_settings(self):
        self.make_file(".coveragerc", self.LOTSA_SETTINGS.format(section=""))
        cov = coverage.coverage()
        self.assert_config_settings_are_correct(cov)

    def test_config_file_settings_in_setupcfg(self):
        # Configuration will be read from setup.cfg from sections prefixed with
        # "coverage:"
        nested = self.LOTSA_SETTINGS.format(section="coverage:")
        self.make_file("setup.cfg", nested + "\n" + self.SETUP_CFG)
        cov = coverage.coverage()
        self.assert_config_settings_are_correct(cov)

    def test_setupcfg_only_if_not_coveragerc(self):
        self.make_file(".coveragerc", """\
            [run]
            include = foo
            """)
        self.make_file("setup.cfg", """\
            [coverage:run]
            omit = bar
            branch = true
            """)
        cov = coverage.coverage()
        self.assertEqual(cov.config.include, ["foo"])
        self.assertEqual(cov.config.omit, None)
        self.assertEqual(cov.config.branch, False)

    def test_setupcfg_only_if_prefixed(self):
        self.make_file("setup.cfg", """\
            [run]
            omit = bar
            branch = true
            """)
        cov = coverage.coverage()
        self.assertEqual(cov.config.omit, None)
        self.assertEqual(cov.config.branch, False)

    def test_non_ascii(self):
        self.make_file(".coveragerc", """\
            [html]
            title = tabblo & «ταБЬℓσ» # numbers
            """)
        cov = coverage.coverage()

        self.assertEqual(cov.config.html_title,
            "tabblo & «ταБЬℓσ» # numbers"
            )
