# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

"""Test cmdline.py for coverage.py."""

import os
import pprint
import re
import sys
import textwrap

import mock
import pytest

import coverage
import coverage.cmdline
from coverage import env
from coverage.config import CoverageConfig
from coverage.data import CoverageData, CoverageDataFiles
from coverage.misc import ExceptionDuringRun

from tests.coveragetest import CoverageTest, OK, ERR, command_line


class BaseCmdLineTest(CoverageTest):
    """Tests of execution paths through the command line interpreter."""

    run_in_temp_dir = False

    # Make a dict mapping function names to the default values that cmdline.py
    # uses when calling the function.
    defaults = mock.Mock()
    defaults.Coverage(
        cover_pylib=None, data_suffix=None, timid=None, branch=None,
        config_file=True, source=None, include=None, omit=None, debug=None,
        concurrency=None, check_preimported=True,
    )
    defaults.annotate(
        directory=None, ignore_errors=None, include=None, omit=None, morfs=[],
    )
    defaults.html_report(
        directory=None, ignore_errors=None, include=None, omit=None, morfs=[],
        skip_covered=None, title=None
    )
    defaults.report(
        ignore_errors=None, include=None, omit=None, morfs=[],
        show_missing=None, skip_covered=None
    )
    defaults.xml_report(
        ignore_errors=None, include=None, omit=None, morfs=[], outfile=None,
    )

    DEFAULT_KWARGS = dict((name, kw) for name, _, kw in defaults.mock_calls)

    def model_object(self):
        """Return a Mock suitable for use in CoverageScript."""
        mk = mock.Mock()
        # We'll invoke .Coverage as the constructor, and then keep using the
        # same object as the resulting coverage object.
        mk.Coverage.return_value = mk

        # The mock needs to get options, but shouldn't need to set them.
        config = CoverageConfig()
        mk.get_option = config.get_option

        # Get the type right for the result of reporting.
        mk.report.return_value = 50.0
        mk.html_report.return_value = 50.0
        mk.xml_report.return_value = 50.0

        return mk

    def mock_command_line(self, args, path_exists=None):
        """Run `args` through the command line, with a Mock.

        Returns the Mock it used and the status code returned.

        """
        m = self.model_object()
        m.path_exists.return_value = path_exists

        ret = command_line(
            args,
            _covpkg=m, _run_python_file=m.run_python_file,
            _run_python_module=m.run_python_module, _help_fn=m.help_fn,
            _path_exists=m.path_exists,
            )

        return m, ret

    def cmd_executes(self, args, code, ret=OK, path_exists=None):
        """Assert that the `args` end up executing the sequence in `code`."""
        m1, r1 = self.mock_command_line(args, path_exists=path_exists)
        self.assertEqual(r1, ret, "Wrong status: got %r, wanted %r" % (r1, ret))

        # Remove all indentation, and change ".foo()" to "m2.foo()".
        code = re.sub(r"(?m)^\s+", "", code)
        code = re.sub(r"(?m)^\.", "m2.", code)
        m2 = self.model_object()
        m2.path_exists.return_value = path_exists
        code_obj = compile(code, "<code>", "exec")
        eval(code_obj, globals(), {'m2': m2})       # pylint: disable=eval-used

        # Many of our functions take a lot of arguments, and cmdline.py
        # calls them with many.  But most of them are just the defaults, which
        # we don't want to have to repeat in all tests.  For each call, apply
        # the defaults.  This lets the tests just mention the interesting ones.
        for name, _, kwargs in m2.method_calls:
            for k, v in self.DEFAULT_KWARGS.get(name, {}).items():
                if k not in kwargs:
                    kwargs[k] = v
        self.assert_same_method_calls(m1, m2)

    def cmd_executes_same(self, args1, args2):
        """Assert that the `args1` executes the same as `args2`."""
        m1, r1 = self.mock_command_line(args1)
        m2, r2 = self.mock_command_line(args2)
        self.assertEqual(r1, r2)
        self.assert_same_method_calls(m1, m2)

    def assert_same_method_calls(self, m1, m2):
        """Assert that `m1.method_calls` and `m2.method_calls` are the same."""
        # Use a real equality comparison, but if it fails, use a nicer assert
        # so we can tell what's going on.  We have to use the real == first due
        # to CmdOptionParser.__eq__
        if m1.method_calls != m2.method_calls:
            pp1 = pprint.pformat(m1.method_calls)
            pp2 = pprint.pformat(m2.method_calls)
            self.assertMultiLineEqual(pp1+'\n', pp2+'\n')

    def cmd_help(self, args, help_msg=None, topic=None, ret=ERR):
        """Run a command line, and check that it prints the right help.

        Only the last function call in the mock is checked, which should be the
        help message that we want to see.

        """
        m, r = self.mock_command_line(args)
        self.assertEqual(r, ret, "Wrong status: got %s, wanted %s" % (r, ret))
        if help_msg:
            self.assertEqual(m.method_calls[-1], ('help_fn', (help_msg,), {}))
        else:
            self.assertEqual(m.method_calls[-1], ('help_fn', (), {'topic': topic}))


class BaseCmdLineTestTest(BaseCmdLineTest):
    """Tests that our BaseCmdLineTest helpers work."""
    def test_assert_same_method_calls(self):
        # All the other tests here use self.cmd_executes_same in successful
        # ways, so here we just check that it fails.
        with self.assertRaises(AssertionError):
            self.cmd_executes_same("run", "debug")


class CmdLineTest(BaseCmdLineTest):
    """Tests of the coverage.py command line."""

    def test_annotate(self):
        # coverage annotate [-d DIR] [-i] [--omit DIR,...] [FILE1 FILE2 ...]
        self.cmd_executes("annotate", """\
            .Coverage()
            .load()
            .annotate()
            """)
        self.cmd_executes("annotate -d dir1", """\
            .Coverage()
            .load()
            .annotate(directory="dir1")
            """)
        self.cmd_executes("annotate -i", """\
            .Coverage()
            .load()
            .annotate(ignore_errors=True)
            """)
        self.cmd_executes("annotate --omit fooey", """\
            .Coverage(omit=["fooey"])
            .load()
            .annotate(omit=["fooey"])
            """)
        self.cmd_executes("annotate --omit fooey,booey", """\
            .Coverage(omit=["fooey", "booey"])
            .load()
            .annotate(omit=["fooey", "booey"])
            """)
        self.cmd_executes("annotate mod1", """\
            .Coverage()
            .load()
            .annotate(morfs=["mod1"])
            """)
        self.cmd_executes("annotate mod1 mod2 mod3", """\
            .Coverage()
            .load()
            .annotate(morfs=["mod1", "mod2", "mod3"])
            """)

    def test_combine(self):
        # coverage combine with args
        self.cmd_executes("combine datadir1", """\
            .Coverage()
            .combine(["datadir1"], strict=True)
            .save()
            """)
        # coverage combine, appending
        self.cmd_executes("combine --append datadir1", """\
            .Coverage()
            .load()
            .combine(["datadir1"], strict=True)
            .save()
            """)
        # coverage combine without args
        self.cmd_executes("combine", """\
            .Coverage()
            .combine(None, strict=True)
            .save()
            """)

    def test_combine_doesnt_confuse_options_with_args(self):
        # https://bitbucket.org/ned/coveragepy/issues/385/coverage-combine-doesnt-work-with-rcfile
        self.cmd_executes("combine --rcfile cov.ini", """\
            .Coverage(config_file='cov.ini')
            .combine(None, strict=True)
            .save()
            """)
        self.cmd_executes("combine --rcfile cov.ini data1 data2/more", """\
            .Coverage(config_file='cov.ini')
            .combine(["data1", "data2/more"], strict=True)
            .save()
            """)

    def test_debug(self):
        self.cmd_help("debug", "What information would you like: config, data, sys?")
        self.cmd_help("debug foo", "Don't know what you mean by 'foo'")

    def test_debug_sys(self):
        self.command_line("debug sys")
        out = self.stdout()
        self.assertIn("version:", out)
        self.assertIn("data_path:", out)

    def test_debug_config(self):
        self.command_line("debug config")
        out = self.stdout()
        self.assertIn("cover_pylib:", out)
        self.assertIn("skip_covered:", out)

    def test_erase(self):
        # coverage erase
        self.cmd_executes("erase", """\
            .Coverage()
            .erase()
            """)

    def test_version(self):
        # coverage --version
        self.cmd_help("--version", topic="version", ret=OK)

    def test_help_option(self):
        # coverage -h
        self.cmd_help("-h", topic="help", ret=OK)
        self.cmd_help("--help", topic="help", ret=OK)

    def test_help_command(self):
        self.cmd_executes("help", ".help_fn(topic='help')")

    def test_cmd_help(self):
        self.cmd_executes("run --help", ".help_fn(parser='<CmdOptionParser:run>')")
        self.cmd_executes_same("help run", "run --help")

    def test_html(self):
        # coverage html -d DIR [-i] [--omit DIR,...] [FILE1 FILE2 ...]
        self.cmd_executes("html", """\
            .Coverage()
            .load()
            .html_report()
            """)
        self.cmd_executes("html -d dir1", """\
            .Coverage()
            .load()
            .html_report(directory="dir1")
            """)
        self.cmd_executes("html -i", """\
            .Coverage()
            .load()
            .html_report(ignore_errors=True)
            """)
        self.cmd_executes("html --omit fooey", """\
            .Coverage(omit=["fooey"])
            .load()
            .html_report(omit=["fooey"])
            """)
        self.cmd_executes("html --omit fooey,booey", """\
            .Coverage(omit=["fooey", "booey"])
            .load()
            .html_report(omit=["fooey", "booey"])
            """)
        self.cmd_executes("html mod1", """\
            .Coverage()
            .load()
            .html_report(morfs=["mod1"])
            """)
        self.cmd_executes("html mod1 mod2 mod3", """\
            .Coverage()
            .load()
            .html_report(morfs=["mod1", "mod2", "mod3"])
            """)
        self.cmd_executes("html --title=Hello_there", """\
            .Coverage()
            .load()
            .html_report(title='Hello_there')
            """)

    def test_report(self):
        # coverage report [-m] [-i] [-o DIR,...] [FILE1 FILE2 ...]
        self.cmd_executes("report", """\
            .Coverage()
            .load()
            .report(show_missing=None)
            """)
        self.cmd_executes("report -i", """\
            .Coverage()
            .load()
            .report(ignore_errors=True)
            """)
        self.cmd_executes("report -m", """\
            .Coverage()
            .load()
            .report(show_missing=True)
            """)
        self.cmd_executes("report --omit fooey", """\
            .Coverage(omit=["fooey"])
            .load()
            .report(omit=["fooey"])
            """)
        self.cmd_executes("report --omit fooey,booey", """\
            .Coverage(omit=["fooey", "booey"])
            .load()
            .report(omit=["fooey", "booey"])
            """)
        self.cmd_executes("report mod1", """\
            .Coverage()
            .load()
            .report(morfs=["mod1"])
            """)
        self.cmd_executes("report mod1 mod2 mod3", """\
            .Coverage()
            .load()
            .report(morfs=["mod1", "mod2", "mod3"])
            """)
        self.cmd_executes("report --skip-covered", """\
            .Coverage()
            .load()
            .report(skip_covered=True)
            """)

    def test_run(self):
        # coverage run [-p] [-L] [--timid] MODULE.py [ARG1 ARG2 ...]

        # run calls coverage.erase first.
        self.cmd_executes("run foo.py", """\
            .Coverage()
            .erase()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .save()
            """)
        # run -a combines with an existing data file before saving.
        self.cmd_executes("run -a foo.py", """\
            .Coverage()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .path_exists('.coverage')
            .combine(data_paths=['.coverage'])
            .save()
            """, path_exists=True)
        # run -a doesn't combine anything if the data file doesn't exist.
        self.cmd_executes("run -a foo.py", """\
            .Coverage()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .path_exists('.coverage')
            .save()
            """, path_exists=False)
        # --timid sets a flag, and program arguments get passed through.
        self.cmd_executes("run --timid foo.py abc 123", """\
            .Coverage(timid=True)
            .erase()
            .start()
            .run_python_file('foo.py', ['foo.py', 'abc', '123'])
            .stop()
            .save()
            """)
        # -L sets a flag, and flags for the program don't confuse us.
        self.cmd_executes("run -p -L foo.py -a -b", """\
            .Coverage(cover_pylib=True, data_suffix=True)
            .erase()
            .start()
            .run_python_file('foo.py', ['foo.py', '-a', '-b'])
            .stop()
            .save()
            """)
        self.cmd_executes("run --branch foo.py", """\
            .Coverage(branch=True)
            .erase()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .save()
            """)
        self.cmd_executes("run --rcfile=myrc.rc foo.py", """\
            .Coverage(config_file="myrc.rc")
            .erase()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .save()
            """)
        self.cmd_executes("run --include=pre1,pre2 foo.py", """\
            .Coverage(include=["pre1", "pre2"])
            .erase()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .save()
            """)
        self.cmd_executes("run --omit=opre1,opre2 foo.py", """\
            .Coverage(omit=["opre1", "opre2"])
            .erase()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .save()
            """)
        self.cmd_executes("run --include=pre1,pre2 --omit=opre1,opre2 foo.py", """\
            .Coverage(include=["pre1", "pre2"], omit=["opre1", "opre2"])
            .erase()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .save()
            """)
        self.cmd_executes("run --source=quux,hi.there,/home/bar foo.py", """\
            .Coverage(source=["quux", "hi.there", "/home/bar"])
            .erase()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .save()
            """)
        self.cmd_executes("run --concurrency=gevent foo.py", """\
            .Coverage(concurrency='gevent')
            .erase()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .save()
            """)
        self.cmd_executes("run --concurrency=multiprocessing foo.py", """\
            .Coverage(concurrency='multiprocessing')
            .erase()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .save()
            """)

    def test_bad_concurrency(self):
        self.command_line("run --concurrency=nothing", ret=ERR)
        err = self.stderr()
        self.assertIn("option --concurrency: invalid choice: 'nothing'", err)

    def test_no_multiple_concurrency(self):
        # You can't use multiple concurrency values on the command line.
        # I would like to have a better message about not allowing multiple
        # values for this option, but optparse is not that flexible.
        self.command_line("run --concurrency=multiprocessing,gevent foo.py", ret=ERR)
        err = self.stderr()
        self.assertIn("option --concurrency: invalid choice: 'multiprocessing,gevent'", err)

    def test_multiprocessing_needs_config_file(self):
        # You can't use command-line args to add options to multiprocessing
        # runs, since they won't make it to the subprocesses. You need to use a
        # config file.
        self.command_line("run --concurrency=multiprocessing --branch foo.py", ret=ERR)
        self.assertIn(
            "Options affecting multiprocessing must be specified in a configuration file.",
            self.stderr()
        )

    def test_run_debug(self):
        self.cmd_executes("run --debug=opt1 foo.py", """\
            .Coverage(debug=["opt1"])
            .erase()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .save()
            """)
        self.cmd_executes("run --debug=opt1,opt2 foo.py", """\
            .Coverage(debug=["opt1","opt2"])
            .erase()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .save()
            """)

    def test_run_module(self):
        self.cmd_executes("run -m mymodule", """\
            .Coverage()
            .erase()
            .start()
            .run_python_module('mymodule', ['mymodule'])
            .stop()
            .save()
            """)
        self.cmd_executes("run -m mymodule -qq arg1 arg2", """\
            .Coverage()
            .erase()
            .start()
            .run_python_module('mymodule', ['mymodule', '-qq', 'arg1', 'arg2'])
            .stop()
            .save()
            """)
        self.cmd_executes("run --branch -m mymodule", """\
            .Coverage(branch=True)
            .erase()
            .start()
            .run_python_module('mymodule', ['mymodule'])
            .stop()
            .save()
            """)
        self.cmd_executes_same("run -m mymodule", "run --module mymodule")

    def test_run_nothing(self):
        self.command_line("run", ret=ERR)
        self.assertIn("Nothing to do", self.stderr())

    def test_cant_append_parallel(self):
        self.command_line("run --append --parallel-mode foo.py", ret=ERR)
        self.assertIn("Can't append to data files in parallel mode.", self.stderr())

    def test_xml(self):
        # coverage xml [-i] [--omit DIR,...] [FILE1 FILE2 ...]
        self.cmd_executes("xml", """\
            .Coverage()
            .load()
            .xml_report()
            """)
        self.cmd_executes("xml -i", """\
            .Coverage()
            .load()
            .xml_report(ignore_errors=True)
            """)
        self.cmd_executes("xml -o myxml.foo", """\
            .Coverage()
            .load()
            .xml_report(outfile="myxml.foo")
            """)
        self.cmd_executes("xml -o -", """\
            .Coverage()
            .load()
            .xml_report(outfile="-")
            """)
        self.cmd_executes("xml --omit fooey", """\
            .Coverage(omit=["fooey"])
            .load()
            .xml_report(omit=["fooey"])
            """)
        self.cmd_executes("xml --omit fooey,booey", """\
            .Coverage(omit=["fooey", "booey"])
            .load()
            .xml_report(omit=["fooey", "booey"])
            """)
        self.cmd_executes("xml mod1", """\
            .Coverage()
            .load()
            .xml_report(morfs=["mod1"])
            """)
        self.cmd_executes("xml mod1 mod2 mod3", """\
            .Coverage()
            .load()
            .xml_report(morfs=["mod1", "mod2", "mod3"])
            """)

    def test_no_arguments_at_all(self):
        self.cmd_help("", topic="minimum_help", ret=OK)

    def test_bad_command(self):
        self.cmd_help("xyzzy", "Unknown command: 'xyzzy'")


class CmdLineWithFilesTest(BaseCmdLineTest):
    """Test the command line in ways that need temp files."""

    run_in_temp_dir = True
    no_files_in_temp_dir = True

    def test_debug_data(self):
        data = CoverageData()
        data.add_lines({
            "file1.py": dict.fromkeys(range(1, 18)),
            "file2.py": dict.fromkeys(range(1, 24)),
        })
        data.add_file_tracers({"file1.py": "a_plugin"})
        data_files = CoverageDataFiles()
        data_files.write(data)

        self.command_line("debug data")
        self.assertMultiLineEqual(self.stdout(), textwrap.dedent("""\
            -- data ------------------------------------------------------
            path: FILENAME
            has_arcs: False

            2 files:
            file1.py: 17 lines [a_plugin]
            file2.py: 23 lines
            """).replace("FILENAME", data_files.filename))

    def test_debug_data_with_no_data(self):
        data_files = CoverageDataFiles()
        self.command_line("debug data")
        self.assertMultiLineEqual(self.stdout(), textwrap.dedent("""\
            -- data ------------------------------------------------------
            path: FILENAME
            No data collected
            """).replace("FILENAME", data_files.filename))


class CmdLineStdoutTest(BaseCmdLineTest):
    """Test the command line with real stdout output."""

    def test_minimum_help(self):
        self.command_line("")
        out = self.stdout()
        self.assertIn("Code coverage for Python.", out)
        self.assertLess(out.count("\n"), 4)

    def test_version(self):
        self.command_line("--version")
        out = self.stdout()
        self.assertIn("ersion ", out)
        if env.C_TRACER:
            self.assertIn("with C extension", out)
        else:
            self.assertIn("without C extension", out)
        self.assertLess(out.count("\n"), 4)

    def test_help_contains_command_name(self):
        # Command name should be present in help output.
        if env.JYTHON:
            self.skipTest("Jython gets mad if you patch sys.argv")
        fake_command_path = "lorem/ipsum/dolor".replace("/", os.sep)
        expected_command_name = "dolor"
        fake_argv = [fake_command_path, "sit", "amet"]
        with mock.patch.object(sys, 'argv', new=fake_argv):
            self.command_line("help")
        out = self.stdout()
        self.assertIn(expected_command_name, out)

    def test_help_contains_command_name_from_package(self):
        # Command package name should be present in help output.
        #
        # When the main module is actually a package's `__main__` module, the resulting command line
        # has the `__main__.py` file's patch as the command name. Instead, the command name should
        # be derived from the package name.

        if env.JYTHON:
            self.skipTest("Jython gets mad if you patch sys.argv")
        fake_command_path = "lorem/ipsum/dolor/__main__.py".replace("/", os.sep)
        expected_command_name = "dolor"
        fake_argv = [fake_command_path, "sit", "amet"]
        with mock.patch.object(sys, 'argv', new=fake_argv):
            self.command_line("help")
        out = self.stdout()
        self.assertIn(expected_command_name, out)

    def test_help(self):
        self.command_line("help")
        out = self.stdout()
        self.assertIn("readthedocs.io", out)
        self.assertGreater(out.count("\n"), 10)

    def test_cmd_help(self):
        self.command_line("help run")
        out = self.stdout()
        self.assertIn("<pyfile>", out)
        self.assertIn("--timid", out)
        self.assertGreater(out.count("\n"), 10)

    def test_unknown_topic(self):
        # Should probably be an ERR return, but meh.
        self.command_line("help foobar")
        self.assertEqual(self.stdout(), "Don't know topic 'foobar'\n")

    def test_error(self):
        self.command_line("fooey kablooey", ret=ERR)
        err = self.stderr()
        self.assertIn("fooey", err)
        self.assertIn("help", err)


class CmdMainTest(CoverageTest):
    """Tests of coverage.cmdline.main(), using mocking for isolation."""

    run_in_temp_dir = False

    class CoverageScriptStub(object):
        """A stub for coverage.cmdline.CoverageScript, used by CmdMainTest."""

        def command_line(self, argv):
            """Stub for command_line, the arg determines what it will do."""
            if argv[0] == 'hello':
                print("Hello, world!")
            elif argv[0] == 'raise':
                try:
                    raise Exception("oh noes!")
                except:
                    raise ExceptionDuringRun(*sys.exc_info())
            elif argv[0] == 'internalraise':
                raise ValueError("coverage is broken")
            elif argv[0] == 'exit':
                sys.exit(23)
            else:
                raise AssertionError("Bad CoverageScriptStub: %r" % (argv,))
            return 0

    def setUp(self):
        super(CmdMainTest, self).setUp()
        old_CoverageScript = coverage.cmdline.CoverageScript
        coverage.cmdline.CoverageScript = self.CoverageScriptStub
        self.addCleanup(setattr, coverage.cmdline, 'CoverageScript', old_CoverageScript)

    def test_normal(self):
        ret = coverage.cmdline.main(['hello'])
        self.assertEqual(ret, 0)
        self.assertEqual(self.stdout(), "Hello, world!\n")

    def test_raise(self):
        ret = coverage.cmdline.main(['raise'])
        self.assertEqual(ret, 1)
        self.assertEqual(self.stdout(), "")
        err = self.stderr().split('\n')
        self.assertEqual(err[0], 'Traceback (most recent call last):')
        self.assertEqual(err[-3], '    raise Exception("oh noes!")')
        self.assertEqual(err[-2], 'Exception: oh noes!')

    def test_internalraise(self):
        with self.assertRaisesRegex(ValueError, "coverage is broken"):
            coverage.cmdline.main(['internalraise'])

    def test_exit(self):
        ret = coverage.cmdline.main(['exit'])
        self.assertEqual(ret, 23)


class CoverageReportingFake(object):
    """A fake Coverage and Coverage.coverage test double."""
    # pylint: disable=missing-docstring
    def __init__(self, report_result, html_result, xml_result):
        self.config = CoverageConfig()
        self.report_result = report_result
        self.html_result = html_result
        self.xml_result = xml_result

    def Coverage(self, *args_unused, **kwargs_unused):
        return self

    def set_option(self, optname, optvalue):
        self.config.set_option(optname, optvalue)

    def get_option(self, optname):
        return self.config.get_option(optname)

    def load(self):
        pass

    def report(self, *args_unused, **kwargs_unused):
        return self.report_result

    def html_report(self, *args_unused, **kwargs_unused):
        return self.html_result

    def xml_report(self, *args_unused, **kwargs_unused):
        return self.xml_result


@pytest.mark.parametrize("results, fail_under, cmd, ret", [
    # Command-line switch properly checks the result of reporting functions.
    ((20, 30, 40), None, "report --fail-under=19", 0),
    ((20, 30, 40), None, "report --fail-under=21", 2),
    ((20, 30, 40), None, "html --fail-under=29", 0),
    ((20, 30, 40), None, "html --fail-under=31", 2),
    ((20, 30, 40), None, "xml --fail-under=39", 0),
    ((20, 30, 40), None, "xml --fail-under=41", 2),
    # Configuration file setting properly checks the result of reporting.
    ((20, 30, 40), 19, "report", 0),
    ((20, 30, 40), 21, "report", 2),
    ((20, 30, 40), 29, "html", 0),
    ((20, 30, 40), 31, "html", 2),
    ((20, 30, 40), 39, "xml", 0),
    ((20, 30, 40), 41, "xml", 2),
    # Command-line overrides configuration.
    ((20, 30, 40), 19, "report --fail-under=21", 2),
])
def test_fail_under(results, fail_under, cmd, ret):
    cov = CoverageReportingFake(*results)
    if fail_under is not None:
        cov.set_option("report:fail_under", fail_under)
    ret_actual = command_line(cmd, _covpkg=cov)
    assert ret_actual == ret
