# coding: utf-8
# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

"""Test the config file handling for coverage.py"""

import sys
import os

import coverage
from coverage.misc import CoverageException

from tests.coveragetest import CoverageTest


class ConfigTest(CoverageTest):
    """Tests of the different sources of configuration settings."""

    def test_default_config(self):
        # Just constructing a coverage() object gets the right defaults.
        cov = coverage.Coverage()
        self.assertFalse(cov.config.timid)
        self.assertFalse(cov.config.branch)
        self.assertEqual(cov.config.data_file, ".coverage")

    def test_arguments(self):
        # Arguments to the constructor are applied to the configuration.
        cov = coverage.Coverage(timid=True, data_file="fooey.dat")
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
        cov = coverage.Coverage()
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
        cov = coverage.Coverage(config_file="my_cov.ini")
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
        cov = coverage.Coverage(config_file=False)
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
        cov = coverage.Coverage(timid=False, data_file=".mycov")
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
        cov = coverage.Coverage()
        self.assertEqual(cov.config.data_file, "fromenv.dat")
        # But the constructor arguments override the environment variable.
        cov = coverage.Coverage(data_file="fromarg.dat")
        self.assertEqual(cov.config.data_file, "fromarg.dat")

    def test_parse_errors(self):
        # Im-parsable values raise CoverageException, with details.
        bad_configs_and_msgs = [
            ("[run]\ntimid = maybe?\n", r"maybe[?]"),
            ("timid = 1\n", r"timid = 1"),
            ("[run\n", r"\[run"),
            ("[report]\nexclude_lines = foo(\n",
                r"Invalid \[report\].exclude_lines value 'foo\(': "
                r"(unbalanced parenthesis|missing \))"),
            ("[report]\npartial_branches = foo[\n",
                r"Invalid \[report\].partial_branches value 'foo\[': "
                r"(unexpected end of regular expression|unterminated character set)"),
            ("[report]\npartial_branches_always = foo***\n",
                r"Invalid \[report\].partial_branches_always value "
                r"'foo\*\*\*': "
                r"multiple repeat"),
        ]

        for bad_config, msg in bad_configs_and_msgs:
            print("Trying %r" % bad_config)
            self.make_file(".coveragerc", bad_config)
            with self.assertRaisesRegex(CoverageException, msg):
                coverage.Coverage()

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
        cov = coverage.Coverage()
        self.assertEqual(cov.config.data_file, "hello-world.fooey")
        self.assertEqual(cov.config.branch, True)
        self.assertEqual(
            cov.config.exclude_list,
            ["the_$one", "anotherZZZ", "xZZZy", "xy", "huh${X}what"]
        )

    def test_tweaks_after_constructor(self):
        # Arguments to the constructor are applied to the configuration.
        cov = coverage.Coverage(timid=True, data_file="fooey.dat")
        cov.set_option("run:timid", False)

        self.assertFalse(cov.config.timid)
        self.assertFalse(cov.config.branch)
        self.assertEqual(cov.config.data_file, "fooey.dat")

        self.assertFalse(cov.get_option("run:timid"))
        self.assertFalse(cov.get_option("run:branch"))
        self.assertEqual(cov.get_option("run:data_file"), "fooey.dat")

    def test_tweak_error_checking(self):
        # Trying to set an unknown config value raises an error.
        cov = coverage.Coverage()
        with self.assertRaises(CoverageException):
            cov.set_option("run:xyzzy", 12)
        with self.assertRaises(CoverageException):
            cov.set_option("xyzzy:foo", 12)
        with self.assertRaises(CoverageException):
            _ = cov.get_option("run:xyzzy")
        with self.assertRaises(CoverageException):
            _ = cov.get_option("xyzzy:foo")

    def test_tweak_plugin_options(self):
        # Plugin options have a more flexible syntax.
        cov = coverage.Coverage()
        cov.set_option("run:plugins", ["fooey.plugin", "xyzzy.coverage.plugin"])
        cov.set_option("fooey.plugin:xyzzy", 17)
        cov.set_option("xyzzy.coverage.plugin:plugh", ["a", "b"])
        with self.assertRaises(CoverageException):
            cov.set_option("no_such.plugin:foo", 23)

        self.assertEqual(cov.get_option("fooey.plugin:xyzzy"), 17)
        self.assertEqual(cov.get_option("xyzzy.coverage.plugin:plugh"), ["a", "b"])
        with self.assertRaises(CoverageException):
            _ = cov.get_option("no_such.plugin:foo")

    def test_unknown_option(self):
        self.make_file(".coveragerc", """\
            [run]
            xyzzy = 17
            """)
        msg = r"Unrecognized option '\[run\] xyzzy=' in config file .coveragerc"
        with self.assertRaisesRegex(CoverageException, msg):
            _ = coverage.Coverage()

    def test_misplaced_option(self):
        self.make_file(".coveragerc", """\
            [report]
            branch = True
            """)
        msg = r"Unrecognized option '\[report\] branch=' in config file .coveragerc"
        with self.assertRaisesRegex(CoverageException, msg):
            _ = coverage.Coverage()

    def test_unknown_option_in_other_ini_file(self):
        self.make_file("setup.cfg", """\
            [coverage:run]
            huh = what?
            """)
        msg = r"Unrecognized option '\[coverage:run\] huh=' in config file setup.cfg"
        with self.assertRaisesRegex(CoverageException, msg):
            _ = coverage.Coverage()


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
        source = myapp
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
        package_depth          =                                17

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
        self.assertEqual(cov.config.source, ["myapp"])

        self.assertEqual(cov.get_exclude_list(), ["if 0:", r"pragma:?\s+no cover", "another_tab"])
        self.assertTrue(cov.config.ignore_errors)
        self.assertEqual(cov.config.include, ["a/", "b/"])
        self.assertEqual(cov.config.omit, ["one", "another", "some_more", "yet_more"])
        self.assertEqual(cov.config.precision, 3)

        self.assertEqual(cov.config.partial_list, [r"pragma:?\s+no branch"])
        self.assertEqual(cov.config.partial_always_list, ["if 0:", "while True:"])
        self.assertEqual(cov.config.plugins, ["plugins.a_plugin", "plugins.another"])
        self.assertTrue(cov.config.show_missing)
        self.assertTrue(cov.config.skip_covered)
        self.assertEqual(cov.config.html_dir, r"c:\tricky\dir.somewhere")
        self.assertEqual(cov.config.extra_css, "something/extra.css")
        self.assertEqual(cov.config.html_title, "Title & nums # nums!")

        self.assertEqual(cov.config.xml_output, "mycov.xml")
        self.assertEqual(cov.config.xml_package_depth, 17)

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
        cov = coverage.Coverage()
        self.assert_config_settings_are_correct(cov)

    def test_config_file_settings_in_setupcfg(self):
        # Configuration will be read from setup.cfg from sections prefixed with
        # "coverage:"
        nested = self.LOTSA_SETTINGS.format(section="coverage:")
        self.make_file("setup.cfg", nested + "\n" + self.SETUP_CFG)
        cov = coverage.Coverage()
        self.assert_config_settings_are_correct(cov)

    def test_config_file_settings_in_setupcfg_if_coveragerc_specified(self):
        # Configuration will be read from setup.cfg from sections prefixed with
        # "coverage:", even if the API said to read from a (non-existent)
        # .coveragerc file.
        nested = self.LOTSA_SETTINGS.format(section="coverage:")
        self.make_file("setup.cfg", nested + "\n" + self.SETUP_CFG)
        cov = coverage.Coverage(config_file=".coveragerc")
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
        cov = coverage.Coverage()
        self.assertEqual(cov.config.include, ["foo"])
        self.assertEqual(cov.config.omit, None)
        self.assertEqual(cov.config.branch, False)

    def test_setupcfg_only_if_prefixed(self):
        self.make_file("setup.cfg", """\
            [run]
            omit = bar
            branch = true
            """)
        cov = coverage.Coverage()
        self.assertEqual(cov.config.omit, None)
        self.assertEqual(cov.config.branch, False)

    def test_non_ascii(self):
        self.make_file(".coveragerc", """\
            [report]
            exclude_lines =
                first
                ✘${TOX_ENVNAME}
                third
            [html]
            title = tabblo & «ταБЬℓσ» # numbers
            """)
        self.set_environ("TOX_ENVNAME", "weirdo")
        cov = coverage.Coverage()

        self.assertEqual(cov.config.exclude_list, ["first", "✘weirdo", "third"])
        self.assertEqual(cov.config.html_title, "tabblo & «ταБЬℓσ» # numbers")

    def test_unreadable_config(self):
        # If a config file is explicitly specified, then it is an error for it
        # to not be readable.
        bad_files = [
            "nosuchfile.txt",
            ".",
        ]
        for bad_file in bad_files:
            msg = "Couldn't read %r as a config file" % bad_file
            with self.assertRaisesRegex(CoverageException, msg):
                coverage.Coverage(config_file=bad_file)

    def test_nocoveragerc_file_when_specified(self):
        cov = coverage.Coverage(config_file=".coveragerc")
        self.assertFalse(cov.config.timid)
        self.assertFalse(cov.config.branch)
        self.assertEqual(cov.config.data_file, ".coverage")
