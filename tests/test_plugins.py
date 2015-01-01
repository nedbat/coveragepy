"""Tests for plugins."""

import os
import sys

from nose.plugins.skip import SkipTest

import coverage
from coverage.control import Plugins

import coverage.plugin

from tests.coveragetest import CoverageTest

# Are we running with the C tracer or not?
C_TRACER = os.getenv('COVERAGE_TEST_TRACER', 'c') == 'c'


class FakeConfig(object):
    """A fake config for use in tests."""

    def __init__(self, plugin, options):
        self.plugin = plugin
        self.options = options
        self.asked_for = []

    def get_plugin_options(self, module):
        """Just return the options for `module` if this is the right module."""
        self.asked_for.append(module)
        if module == self.plugin:
            return self.options
        else:
            return {}


class LoadPluginsTest(CoverageTest):
    """Test Plugins.load_plugins directly."""

    def test_importing_and_configuring(self):
        self.make_file("plugin1.py", """\
            from coverage import CoveragePlugin

            class Plugin(CoveragePlugin):
                def __init__(self, options):
                    super(Plugin, self).__init__(options)
                    self.this_is = "me"
            """)

        config = FakeConfig("plugin1", {'a': 'hello'})
        plugins = list(Plugins.load_plugins(["plugin1"], config))

        self.assertEqual(len(plugins), 1)
        self.assertEqual(plugins[0].this_is, "me")
        self.assertEqual(plugins[0].options, {'a': 'hello'})
        self.assertEqual(config.asked_for, ['plugin1'])

    def test_importing_and_configuring_more_than_one(self):
        self.make_file("plugin1.py", """\
            from coverage import CoveragePlugin

            class Plugin(CoveragePlugin):
                def __init__(self, options):
                    super(Plugin, self).__init__(options)
                    self.this_is = "me"
            """)
        self.make_file("plugin2.py", """\
            from coverage import CoveragePlugin

            class Plugin(CoveragePlugin):
                pass
            """)

        config = FakeConfig("plugin1", {'a': 'hello'})
        plugins = list(Plugins.load_plugins(["plugin1", "plugin2"], config))

        self.assertEqual(len(plugins), 2)
        self.assertEqual(plugins[0].this_is, "me")
        self.assertEqual(plugins[0].options, {'a': 'hello'})
        self.assertEqual(plugins[1].options, {})
        self.assertEqual(config.asked_for, ['plugin1', 'plugin2'])

        # The order matters...
        config = FakeConfig("plugin1", {'a': 'second'})
        plugins = list(Plugins.load_plugins(["plugin2", "plugin1"], config))

        self.assertEqual(len(plugins), 2)
        self.assertEqual(plugins[0].options, {})
        self.assertEqual(plugins[1].this_is, "me")
        self.assertEqual(plugins[1].options, {'a': 'second'})

    def test_cant_import(self):
        with self.assertRaises(ImportError):
            _ = Plugins.load_plugins(["plugin_not_there"], None)

    def test_ok_to_not_define_plugin(self):
        # TODO: should this actually be an error or warning?
        self.make_file("plugin2.py", """\
            from coverage import CoveragePlugin

            Nothing = 0
            """)
        plugins = list(Plugins.load_plugins(["plugin2"], None))
        self.assertEqual(plugins, [])


class PluginTest(CoverageTest):
    """Test plugins through the Coverage class."""

    def test_plugin_imported(self):
        # Prove that a plugin will be imported.
        self.make_file("my_plugin.py", """\
            with open("evidence.out", "w") as f:
                f.write("we are here!")
            """)

        self.assert_doesnt_exist("evidence.out")
        cov = coverage.Coverage()
        cov.config["run:plugins"] = ["my_plugin"]
        cov.start()
        cov.stop()

        with open("evidence.out") as f:
            self.assertEqual(f.read(), "we are here!")

    def test_missing_plugin_raises_import_error(self):
        # Prove that a missing plugin will raise an ImportError.
        with self.assertRaises(ImportError):
            cov = coverage.Coverage()
            cov.config["run:plugins"] = ["does_not_exist_woijwoicweo"]
            cov.start()
        cov.stop()

    def test_bad_plugin_isnt_hidden(self):
        # Prove that a plugin with an error in it will raise the error.
        self.make_file("plugin_over_zero.py", """\
            1/0
            """)
        with self.assertRaises(ZeroDivisionError):
            cov = coverage.Coverage()
            cov.config["run:plugins"] = ["plugin_over_zero"]
            cov.start()
        cov.stop()


if not C_TRACER:
    class FileTracerTest(CoverageTest):
        """Tests of plugins that implement file_tracer."""

        def test_plugin1(self):
            if sys.platform == 'win32':
                raise SkipTest("Plugin stuff is jank on windows.. fixing soon...")

            self.make_file("simple.py", """\
                import try_xyz
                a = 1
                b = 2
                """)
            self.make_file("try_xyz.py", """\
                c = 3
                d = 4
                """)

            cov = coverage.Coverage()
            snoop_on_callbacks(cov)
            cov.config["run:plugins"] = ["tests.plugin1"]

            # Import the Python file, executing it.
            self.start_import_stop(cov, "simple")

            _, statements, missing, _ = cov.analysis("simple.py")
            self.assertEqual(statements, [1, 2, 3])
            self.assertEqual(missing, [])
            _, statements, _, _ = cov.analysis("/src/try_ABC.zz")
            self.assertEqual(statements, [105, 106, 107, 205, 206, 207])

        def test_plugin2(self):
            # plugin2 emulates a dynamic tracing plugin: the caller's locals
            # are examined to determine the source file and line number.
            # The plugin is in tests/plugin2.py.
            self.make_file("render.py", """\
                def render(filename, linenum):
                    # This function emulates a template renderer. The plugin
                    # will examine the `filename` and `linenum` locals to
                    # determine the source file and line number.
                    fiddle_around = 1   # not used, just chaff.
                    return "[{0} @ {1}]".format(filename, linenum)

                def helper(x):
                    # This function is here just to show that not all code in
                    # this file will be part of the dynamic tracing.
                    return x+1
                """)
            self.make_file("caller.py", """\
                from render import helper, render

                assert render("foo_7.html", 4) == "[foo_7.html @ 4]"
                # Render foo_7.html again to trigger the callback snoopers.
                render("foo_7.html", 4)

                assert helper(42) == 43
                assert render("bar_4.html", 2) == "[bar_4.html @ 2]"
                assert helper(76) == 77
                """)

            cov = coverage.Coverage()
            snoop_on_callbacks(cov)
            cov.config["run:plugins"] = ["tests.plugin2"]

            self.start_import_stop(cov, "caller")

            # The way plugin2 works, a file named foo_7.html will be claimed to
            # have 7 lines in it.  If render() was called with line number 4,
            # then the plugin will claim that lines 4 and 5 were executed.
            _, statements, missing, _ = cov.analysis("foo_7.html")
            self.assertEqual(statements, [1, 2, 3, 4, 5, 6, 7])
            self.assertEqual(missing, [1, 2, 3, 6, 7])
            _, statements, missing, _ = cov.analysis("bar_4.html")
            self.assertEqual(statements, [1, 2, 3, 4])
            self.assertEqual(missing, [1, 4])


def snoop_on_callbacks(cov):
    cov_should_trace = cov._should_trace
    should_trace_filenames = set()

    def snoop_should_trace(filename, frame):
        assert filename not in should_trace_filenames
        should_trace_filenames.add(filename)
        return cov_should_trace(filename, frame)
    cov._should_trace = snoop_should_trace

    cov_check_include = cov._check_include_omit_etc
    check_include_filenames = set()

    def snoop_check_include_filenames(filename, frame):
        assert filename not in check_include_filenames
        check_include_filenames.add(filename)
        return cov_check_include(filename, frame)
    cov._check_include_omit_etc = snoop_check_include_filenames
