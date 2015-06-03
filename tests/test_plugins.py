"""Tests for plugins."""

import os.path

import coverage
from coverage import env
from coverage.backward import StringIO
from coverage.control import Plugins
from coverage.misc import CoverageException

import coverage.plugin

from tests.coveragetest import CoverageTest
from tests.helpers import CheckUniqueFilenames


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

    def test_implicit_boolean(self):
        self.make_file("plugin1.py", """\
            from coverage import CoveragePlugin

            class Plugin(CoveragePlugin):
                pass
            """)

        config = FakeConfig("plugin1", {})
        plugins = Plugins.load_plugins([], config)
        self.assertFalse(plugins)

        plugins = Plugins.load_plugins(["plugin1"], config)
        self.assertTrue(plugins)

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

    def test_plugin_must_define_plugin_class(self):
        self.make_file("no_plugin.py", """\
            from coverage import CoveragePlugin
            Nothing = 0
            """)
        msg_pat = "Plugin module 'no_plugin' didn't define a Plugin class"
        with self.assertRaisesRegex(CoverageException, msg_pat):
            list(Plugins.load_plugins(["no_plugin"], None))


class PluginTest(CoverageTest):
    """Test plugins through the Coverage class."""

    def test_plugin_imported(self):
        # Prove that a plugin will be imported.
        self.make_file("my_plugin.py", """\
            from coverage import CoveragePlugin
            class Plugin(CoveragePlugin):
                pass
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

    def test_plugin_sys_info(self):
        self.make_file("plugin_sys_info.py", """\
            import coverage

            class Plugin(coverage.CoveragePlugin):
                def sys_info(self):
                    return [("hello", "world")]
            """)
        debug_out = StringIO()
        cov = coverage.Coverage(debug=["sys"])
        cov._debug_file = debug_out
        cov.config["run:plugins"] = ["plugin_sys_info"]
        cov.load()

        out_lines = debug_out.getvalue().splitlines()
        expected_end = [
            "-- sys: plugin_sys_info --------------------------------------",
            " hello: world",
            "-- end -------------------------------------------------------",
            ]
        self.assertEqual(expected_end, out_lines[-len(expected_end):])

    def test_plugin_with_no_sys_info(self):
        self.make_file("plugin_no_sys_info.py", """\
            import coverage

            class Plugin(coverage.CoveragePlugin):
                pass
            """)
        debug_out = StringIO()
        cov = coverage.Coverage(debug=["sys"])
        cov._debug_file = debug_out
        cov.config["run:plugins"] = ["plugin_no_sys_info"]
        cov.load()

        out_lines = debug_out.getvalue().splitlines()
        expected_end = [
            "-- sys: plugin_no_sys_info -----------------------------------",
            "-- end -------------------------------------------------------",
            ]
        self.assertEqual(expected_end, out_lines[-len(expected_end):])

    def test_local_files_are_importable(self):
        self.make_file("importing_plugin.py", """\
            from coverage import CoveragePlugin
            import local_module
            class Plugin(CoveragePlugin):
                pass
            """)
        self.make_file("local_module.py", "CONST = 1")
        self.make_file(".coveragerc", """\
            [run]
            plugins = importing_plugin
            """)
        self.make_file("main_file.py", "print('MAIN')")

        out = self.run_command("coverage run main_file.py")
        self.assertEqual(out, "MAIN\n")
        out = self.run_command("coverage html")
        self.assertEqual(out, "")


class PluginWarningOnPyTracer(CoverageTest):
    """Test that we get a controlled exception with plugins on PyTracer."""
    def setUp(self):
        super(PluginWarningOnPyTracer, self).setUp()
        if env.C_TRACER:
            self.skip("This test is only about PyTracer.")

    def test_exception_if_plugins_on_pytracer(self):
        self.make_file("simple.py", """a = 1""")

        cov = coverage.Coverage()
        cov.config["run:plugins"] = ["tests.plugin1"]

        warnings = []
        def capture_warning(msg):
            warnings.append(msg)
        cov._warn = capture_warning

        self.start_import_stop(cov, "simple")
        self.assertIn(
            "Plugin file tracers (tests.plugin1) "
            "aren't supported with PyTracer",
            warnings
        )


class FileTracerTest(CoverageTest):
    """Tests of plugins that implement file_tracer."""

    def setUp(self):
        super(FileTracerTest, self).setUp()
        if not env.C_TRACER:
            self.skip("Plugins are only supported with the C tracer.")


class GoodPluginTest(FileTracerTest):
    """Tests of plugin happy paths."""

    def test_plugin1(self):
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
        CheckUniqueFilenames.hook(cov, '_should_trace')
        CheckUniqueFilenames.hook(cov, '_check_include_omit_etc')
        cov.config["run:plugins"] = ["tests.plugin1"]

        # Import the Python file, executing it.
        self.start_import_stop(cov, "simple")

        _, statements, missing, _ = cov.analysis("simple.py")
        self.assertEqual(statements, [1, 2, 3])
        self.assertEqual(missing, [])
        zzfile = os.path.abspath(os.path.join("/src", "try_ABC.zz"))
        _, statements, _, _ = cov.analysis(zzfile)
        self.assertEqual(statements, [105, 106, 107, 205, 206, 207])

    def make_render_and_caller(self):
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
            import sys
            from render import helper, render

            assert render("foo_7.html", 4) == "[foo_7.html @ 4]"
            # Render foo_7.html again to try the CheckUniqueFilenames asserts.
            render("foo_7.html", 4)

            assert helper(42) == 43
            assert render("bar_4.html", 2) == "[bar_4.html @ 2]"
            assert helper(76) == 77

            # quux_5.html will be omitted from the results.
            assert render("quux_5.html", 3) == "[quux_5.html @ 3]"

            # In Python 2, either kind of string should be OK.
            if sys.version_info[0] == 2:
                assert render(u"uni_3.html", 2) == "[uni_3.html @ 2]"
            """)

        # will try to read the actual source files, so make some
        # source files.
        def lines(n):
            """Make a string with n lines of text."""
            return "".join("line %d\n" % i for i in range(n))

        self.make_file("bar_4.html", lines(4))
        self.make_file("foo_7.html", lines(7))

    def test_plugin2(self):
        self.make_render_and_caller()

        cov = coverage.Coverage(omit=["*quux*"])
        CheckUniqueFilenames.hook(cov, '_should_trace')
        CheckUniqueFilenames.hook(cov, '_check_include_omit_etc')
        cov.config["run:plugins"] = ["tests.plugin2"]

        self.start_import_stop(cov, "caller")

        # The way plugin2 works, a file named foo_7.html will be claimed to
        # have 7 lines in it.  If render() was called with line number 4,
        # then the plugin will claim that lines 4 and 5 were executed.
        _, statements, missing, _ = cov.analysis("foo_7.html")
        self.assertEqual(statements, [1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(missing, [1, 2, 3, 6, 7])
        self.assertIn("foo_7.html", cov.data.summary())

        _, statements, missing, _ = cov.analysis("bar_4.html")
        self.assertEqual(statements, [1, 2, 3, 4])
        self.assertEqual(missing, [1, 4])
        self.assertIn("bar_4.html", cov.data.summary())

        self.assertNotIn("quux_5.html", cov.data.summary())

        if env.PY2:
            _, statements, missing, _ = cov.analysis("uni_3.html")
            self.assertEqual(statements, [1, 2, 3])
            self.assertEqual(missing, [1])
            self.assertIn("uni_3.html", cov.data.summary())

    def test_plugin2_with_branch(self):
        self.make_render_and_caller()

        cov = coverage.Coverage(branch=True, omit=["*quux*"])
        CheckUniqueFilenames.hook(cov, '_should_trace')
        CheckUniqueFilenames.hook(cov, '_check_include_omit_etc')
        cov.config["run:plugins"] = ["tests.plugin2"]

        self.start_import_stop(cov, "caller")

        # The way plugin2 works, a file named foo_7.html will be claimed to
        # have 7 lines in it.  If render() was called with line number 4,
        # then the plugin will claim that lines 4 and 5 were executed.
        analysis = cov._analyze("foo_7.html")
        self.assertEqual(analysis.statements, set([1, 2, 3, 4, 5, 6, 7]))
        # Plugins don't do branch coverage yet.
        self.assertEqual(analysis.has_arcs(), True)
        self.assertEqual(analysis.arc_possibilities(), [])

        self.assertEqual(analysis.missing, set([1, 2, 3, 6, 7]))

    def test_plugin2_with_text_report(self):
        self.make_render_and_caller()

        cov = coverage.Coverage(branch=True, omit=["*quux*"])
        cov.config["run:plugins"] = ["tests.plugin2"]

        self.start_import_stop(cov, "caller")

        repout = StringIO()
        total = cov.report(file=repout, include=["*.html"], omit=["uni*.html"])
        report = repout.getvalue().splitlines()
        expected = [
            'Name         Stmts   Miss Branch BrPart  Cover   Missing',
            '--------------------------------------------------------',
            'bar_4.html       4      2      0      0    50%   1, 4',
            'foo_7.html       7      5      0      0    29%   1-3, 6-7',
            '--------------------------------------------------------',
            'TOTAL           11      7      0      0    36%   ',
            ]
        self.assertEqual(report, expected)
        self.assertAlmostEqual(total, 36.36, places=2)

    def test_plugin2_with_html_report(self):
        self.make_render_and_caller()

        cov = coverage.Coverage(branch=True, omit=["*quux*"])
        cov.config["run:plugins"] = ["tests.plugin2"]

        self.start_import_stop(cov, "caller")

        total = cov.html_report(include=["*.html"], omit=["uni*.html"])
        self.assertAlmostEqual(total, 36.36, places=2)

        self.assert_exists("htmlcov/index.html")
        self.assert_exists("htmlcov/bar_4_html.html")
        self.assert_exists("htmlcov/foo_7_html.html")

    def test_plugin2_with_xml_report(self):
        self.make_render_and_caller()

        cov = coverage.Coverage(branch=True, omit=["*quux*"])
        cov.config["run:plugins"] = ["tests.plugin2"]

        self.start_import_stop(cov, "caller")

        total = cov.xml_report(include=["*.html"], omit=["uni*.html"])
        self.assertAlmostEqual(total, 36.36, places=2)

        with open("coverage.xml") as fxml:
            xml = fxml.read()

        for snip in [
            'filename="bar_4.html" line-rate="0.5" name="bar_4.html"',
            'filename="foo_7.html" line-rate="0.2857" name="foo_7.html"',
            ]:
            self.assertIn(snip, xml)


class BadPluginTest(FileTracerTest):
    """Test error handling around plugins."""

    def run_bad_plugin(self, plugin_name, our_error=True):
        """Run a file, and see that the plugin failed.

        `plugin_name` is the name of the plugin to use.

        `our_error` is True if the error reported to the user will be an
        explicit error in our test code, marked with an # Oh noes! comment.

        """
        self.make_file("simple.py", """\
            import other, another
            a = other.f(2)
            b = other.f(3)
            c = another.g(4)
            d = another.g(5)
            """)
        # The names of these files are important: some plugins apply themselves
        # to "*other.py".
        self.make_file("other.py", """\
            def f(x):
                return x+1
            """)
        self.make_file("another.py", """\
            def g(x):
                return x-1
            """)

        cov = coverage.Coverage()
        cov.config["run:plugins"] = [plugin_name]
        self.start_import_stop(cov, "simple")

        stderr = self.stderr()
        print(stderr)           # for diagnosing test failures.

        if our_error:
            errors = stderr.count("# Oh noes!")
            # The exception we're causing should only appear once.
            self.assertEqual(errors, 1)

        # There should be a warning explaining what's happening, but only one.
        # The message can be in two forms:
        #   Disabling plugin '...' due to previous exception
        # or:
        #   Disabling plugin '...' due to an excepton:
        msg = "Disabling plugin %r due to " % plugin_name
        warnings = stderr.count(msg)
        self.assertEqual(warnings, 1)

    def test_file_tracer_fails(self):
        self.make_file("bad_plugin.py", """\
            import coverage.plugin
            class Plugin(coverage.plugin.CoveragePlugin):
                def file_tracer(self, filename):
                    17/0 # Oh noes!
            """)
        self.run_bad_plugin("bad_plugin")

    def test_file_tracer_returns_wrong(self):
        self.make_file("bad_plugin.py", """\
            import coverage.plugin
            class Plugin(coverage.plugin.CoveragePlugin):
                def file_tracer(self, filename):
                    return 3.14159
            """)
        self.run_bad_plugin("bad_plugin", our_error=False)

    def test_has_dynamic_source_filename_fails(self):
        self.make_file("bad_plugin.py", """\
            import coverage.plugin
            class Plugin(coverage.plugin.CoveragePlugin):
                def file_tracer(self, filename):
                    return BadFileTracer()

            class BadFileTracer(coverage.plugin.FileTracer):
                def has_dynamic_source_filename(self):
                    23/0 # Oh noes!
            """)
        self.run_bad_plugin("bad_plugin")

    def test_source_filename_fails(self):
        self.make_file("bad_plugin.py", """\
            import coverage.plugin
            class Plugin(coverage.plugin.CoveragePlugin):
                def file_tracer(self, filename):
                    return BadFileTracer()

            class BadFileTracer(coverage.plugin.FileTracer):
                def source_filename(self):
                    42/0 # Oh noes!
            """)
        self.run_bad_plugin("bad_plugin")

    def test_source_filename_returns_wrong(self):
        self.make_file("bad_plugin.py", """\
            import coverage.plugin
            class Plugin(coverage.plugin.CoveragePlugin):
                def file_tracer(self, filename):
                    return BadFileTracer()

            class BadFileTracer(coverage.plugin.FileTracer):
                def source_filename(self):
                    return 17.3
            """)
        self.run_bad_plugin("bad_plugin", our_error=False)

    def test_dynamic_source_filename_fails(self):
        self.make_file("bad_plugin.py", """\
            import coverage.plugin
            class Plugin(coverage.plugin.CoveragePlugin):
                def file_tracer(self, filename):
                    if filename.endswith("other.py"):
                        return BadFileTracer()

            class BadFileTracer(coverage.plugin.FileTracer):
                def has_dynamic_source_filename(self):
                    return True
                def dynamic_source_filename(self, filename, frame):
                    101/0 # Oh noes!
            """)
        self.run_bad_plugin("bad_plugin")

    def test_line_number_range_returns_non_tuple(self):
        self.make_file("bad_plugin.py", """\
            import coverage.plugin
            class Plugin(coverage.plugin.CoveragePlugin):
                def file_tracer(self, filename):
                    if filename.endswith("other.py"):
                        return BadFileTracer()

            class BadFileTracer(coverage.plugin.FileTracer):
                def source_filename(self):
                    return "something.foo"

                def line_number_range(self, frame):
                    return 42.23
            """)
        self.run_bad_plugin("bad_plugin", our_error=False)

    def test_line_number_range_returns_triple(self):
        self.make_file("bad_plugin.py", """\
            import coverage.plugin
            class Plugin(coverage.plugin.CoveragePlugin):
                def file_tracer(self, filename):
                    if filename.endswith("other.py"):
                        return BadFileTracer()

            class BadFileTracer(coverage.plugin.FileTracer):
                def source_filename(self):
                    return "something.foo"

                def line_number_range(self, frame):
                    return (1, 2, 3)
            """)
        self.run_bad_plugin("bad_plugin", our_error=False)

    def test_line_number_range_returns_pair_of_strings(self):
        self.make_file("bad_plugin.py", """\
            import coverage.plugin
            class Plugin(coverage.plugin.CoveragePlugin):
                def file_tracer(self, filename):
                    if filename.endswith("other.py"):
                        return BadFileTracer()

            class BadFileTracer(coverage.plugin.FileTracer):
                def source_filename(self):
                    return "something.foo"

                def line_number_range(self, frame):
                    return ("5", "7")
            """)
        self.run_bad_plugin("bad_plugin", our_error=False)
