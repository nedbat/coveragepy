"""Tests for plugins."""

import coverage
from coverage.plugin import load_plugins

from tests.coveragetest import CoverageTest


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


class PluginUnitTest(CoverageTest):
    """Test load_plugins directly."""

    def test_importing_and_configuring(self):
        self.make_file("plugin1.py", """\
            from coverage.plugin import CoveragePlugin

            class Plugin(CoveragePlugin):
                def __init__(self, options):
                    super(Plugin, self).__init__(options)
                    self.this_is = "me"
            """)

        config = FakeConfig("plugin1", {'a':'hello'})
        plugins = load_plugins(["plugin1"], config)

        self.assertEqual(len(plugins), 1)
        self.assertEqual(plugins[0].this_is, "me")
        self.assertEqual(plugins[0].options, {'a':'hello'})
        self.assertEqual(config.asked_for, ['plugin1'])

    def test_importing_and_configuring_more_than_one(self):
        self.make_file("plugin1.py", """\
            from coverage.plugin import CoveragePlugin

            class Plugin(CoveragePlugin):
                def __init__(self, options):
                    super(Plugin, self).__init__(options)
                    self.this_is = "me"
            """)
        self.make_file("plugin2.py", """\
            from coverage.plugin import CoveragePlugin

            class Plugin(CoveragePlugin):
                pass
            """)

        config = FakeConfig("plugin1", {'a':'hello'})
        plugins = load_plugins(["plugin1", "plugin2"], config)

        self.assertEqual(len(plugins), 2)
        self.assertEqual(plugins[0].this_is, "me")
        self.assertEqual(plugins[0].options, {'a':'hello'})
        self.assertEqual(plugins[1].options, {})
        self.assertEqual(config.asked_for, ['plugin1', 'plugin2'])

    def test_cant_import(self):
        with self.assertRaises(ImportError):
            _ = load_plugins(["plugin_not_there"], None)

    def test_ok_to_not_define_plugin(self):
        self.make_file("plugin2.py", """\
            from coverage.plugin import CoveragePlugin

            Nothing = 0
            """)
        plugins = load_plugins(["plugin2"], None)
        self.assertEqual(plugins, [])


class PluginTest(CoverageTest):
    """Test plugins through the Coverage class."""

    def test_plugin_imported(self):
        self.make_file("my_plugin.py", """\
            with open("evidence.out", "w") as f:
                f.write("we are here!")
            """)

        self.assert_doesnt_exist("evidence.out")
        _ = coverage.Coverage(plugins=["my_plugin"])

        with open("evidence.out") as f:
            self.assertEqual(f.read(), "we are here!")

    def test_bad_plugin_raises_import_error(self):
        with self.assertRaises(ImportError):
            cov = coverage.Coverage(plugins=["foo"])
            cov.start()
