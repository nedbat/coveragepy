# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

"""Test cmdline.py for coverage.py."""

import pprint
import re
import shlex
import sys
import textwrap

import mock

import coverage
import coverage.cmdline
from coverage import env
from coverage.config import CoverageConfig
from coverage.data import CoverageData, CoverageDataFiles
from coverage.misc import CoverageException, ExceptionDuringRun

from tests.coveragetest import CoverageTest, OK, ERR


class BaseCmdLineTest(CoverageTest):
    """Tests of execution paths through the command line interpreter."""

    run_in_temp_dir = False

    # Make a dict mapping function names to the default values that cmdline.py
    # uses when calling the function.
    defaults = mock.Mock()
    defaults.coverage(
        cover_pylib=None, data_suffix=None, timid=None, branch=None,
        config_file=True, source=None, include=None, omit=None, debug=None,
        concurrency=None,
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
        # We'll invoke .coverage as the constructor, and then keep using the
        # same object as the resulting coverage object.
        mk.coverage.return_value = mk

        # The mock needs to get options, but shouldn't need to set them.
        config = CoverageConfig()
        mk.get_option = config.get_option

        return mk

    def mock_command_line(self, args, path_exists=None):
        """Run `args` through the command line, with a Mock.

        Returns the Mock it used and the status code returned.

        """
        m = self.model_object()
        m.path_exists.return_value = path_exists

        ret = coverage.cmdline.CoverageScript(
            _covpkg=m, _run_python_file=m.run_python_file,
            _run_python_module=m.run_python_module, _help_fn=m.help_fn,
            _path_exists=m.path_exists,
            ).command_line(shlex.split(args))

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
        for name, args, kwargs in m2.method_calls:
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
            .coverage()
            .load()
            .annotate()
            """)
        self.cmd_executes("annotate -d dir1", """\
            .coverage()
            .load()
            .annotate(directory="dir1")
            """)
        self.cmd_executes("annotate -i", """\
            .coverage()
            .load()
            .annotate(ignore_errors=True)
            """)
        self.cmd_executes("annotate --omit fooey", """\
            .coverage(omit=["fooey"])
            .load()
            .annotate(omit=["fooey"])
            """)
        self.cmd_executes("annotate --omit fooey,booey", """\
            .coverage(omit=["fooey", "booey"])
            .load()
            .annotate(omit=["fooey", "booey"])
            """)
        self.cmd_executes("annotate mod1", """\
            .coverage()
            .load()
            .annotate(morfs=["mod1"])
            """)
        self.cmd_executes("annotate mod1 mod2 mod3", """\
            .coverage()
            .load()
            .annotate(morfs=["mod1", "mod2", "mod3"])
            """)

    def test_combine(self):
        # coverage combine with args
        self.cmd_executes("combine datadir1", """\
            .coverage()
            .combine(["datadir1"], strict=True)
            .save()
            """)
        # coverage combine, appending
        self.cmd_executes("combine --append datadir1", """\
            .coverage()
            .load()
            .combine(["datadir1"], strict=True)
            .save()
            """)
        # coverage combine without args
        self.cmd_executes("combine", """\
            .coverage()
            .combine(None, strict=True)
            .save()
            """)

    def test_combine_doesnt_confuse_options_with_args(self):
        # https://bitbucket.org/ned/coveragepy/issues/385/coverage-combine-doesnt-work-with-rcfile
        self.cmd_executes("combine --rcfile cov.ini", """\
            .coverage(config_file='cov.ini')
            .combine(None, strict=True)
            .save()
            """)
        self.cmd_executes("combine --rcfile cov.ini data1 data2/more", """\
            .coverage(config_file='cov.ini')
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
            .coverage()
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
            .coverage()
            .load()
            .html_report()
            """)
        self.cmd_executes("html -d dir1", """\
            .coverage()
            .load()
            .html_report(directory="dir1")
            """)
        self.cmd_executes("html -i", """\
            .coverage()
            .load()
            .html_report(ignore_errors=True)
            """)
        self.cmd_executes("html --omit fooey", """\
            .coverage(omit=["fooey"])
            .load()
            .html_report(omit=["fooey"])
            """)
        self.cmd_executes("html --omit fooey,booey", """\
            .coverage(omit=["fooey", "booey"])
            .load()
            .html_report(omit=["fooey", "booey"])
            """)
        self.cmd_executes("html mod1", """\
            .coverage()
            .load()
            .html_report(morfs=["mod1"])
            """)
        self.cmd_executes("html mod1 mod2 mod3", """\
            .coverage()
            .load()
            .html_report(morfs=["mod1", "mod2", "mod3"])
            """)
        self.cmd_executes("html --title=Hello_there", """\
            .coverage()
            .load()
            .html_report(title='Hello_there')
            """)

    def test_report(self):
        # coverage report [-m] [-i] [-o DIR,...] [FILE1 FILE2 ...]
        self.cmd_executes("report", """\
            .coverage()
            .load()
            .report(show_missing=None)
            """)
        self.cmd_executes("report -i", """\
            .coverage()
            .load()
            .report(ignore_errors=True)
            """)
        self.cmd_executes("report -m", """\
            .coverage()
            .load()
            .report(show_missing=True)
            """)
        self.cmd_executes("report --omit fooey", """\
            .coverage(omit=["fooey"])
            .load()
            .report(omit=["fooey"])
            """)
        self.cmd_executes("report --omit fooey,booey", """\
            .coverage(omit=["fooey", "booey"])
            .load()
            .report(omit=["fooey", "booey"])
            """)
        self.cmd_executes("report mod1", """\
            .coverage()
            .load()
            .report(morfs=["mod1"])
            """)
        self.cmd_executes("report mod1 mod2 mod3", """\
            .coverage()
            .load()
            .report(morfs=["mod1", "mod2", "mod3"])
            """)
        self.cmd_executes("report --skip-covered", """\
            .coverage()
            .load()
            .report(skip_covered=True)
            """)

    def test_run(self):
        # coverage run [-p] [-L] [--timid] MODULE.py [ARG1 ARG2 ...]

        # run calls coverage.erase first.
        self.cmd_executes("run foo.py", """\
            .coverage()
            .erase()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .save()
            """)
        # run -a combines with an existing data file before saving.
        self.cmd_executes("run -a foo.py", """\
            .coverage()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .path_exists('.coverage')
            .combine(data_paths=['.coverage'])
            .save()
            """, path_exists=True)
        # run -a doesn't combine anything if the data file doesn't exist.
        self.cmd_executes("run -a foo.py", """\
            .coverage()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .path_exists('.coverage')
            .save()
            """, path_exists=False)
        # --timid sets a flag, and program arguments get passed through.
        self.cmd_executes("run --timid foo.py abc 123", """\
            .coverage(timid=True)
            .erase()
            .start()
            .run_python_file('foo.py', ['foo.py', 'abc', '123'])
            .stop()
            .save()
            """)
        # -L sets a flag, and flags for the program don't confuse us.
        self.cmd_executes("run -p -L foo.py -a -b", """\
            .coverage(cover_pylib=True, data_suffix=True)
            .erase()
            .start()
            .run_python_file('foo.py', ['foo.py', '-a', '-b'])
            .stop()
            .save()
            """)
        self.cmd_executes("run --branch foo.py", """\
            .coverage(branch=True)
            .erase()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .save()
            """)
        self.cmd_executes("run --rcfile=myrc.rc foo.py", """\
            .coverage(config_file="myrc.rc")
            .erase()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .save()
            """)
        self.cmd_executes("run --include=pre1,pre2 foo.py", """\
            .coverage(include=["pre1", "pre2"])
            .erase()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .save()
            """)
        self.cmd_executes("run --omit=opre1,opre2 foo.py", """\
            .coverage(omit=["opre1", "opre2"])
            .erase()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .save()
            """)
        self.cmd_executes("run --include=pre1,pre2 --omit=opre1,opre2 foo.py", """\
            .coverage(include=["pre1", "pre2"], omit=["opre1", "opre2"])
            .erase()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .save()
            """)
        self.cmd_executes("run --source=quux,hi.there,/home/bar foo.py", """\
            .coverage(source=["quux", "hi.there", "/home/bar"])
            .erase()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .save()
            """)
        self.cmd_executes("run --concurrency=gevent foo.py", """\
            .coverage(concurrency='gevent')
            .erase()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .save()
            """)
        self.cmd_executes("run --concurrency=multiprocessing foo.py", """\
            .coverage(concurrency='multiprocessing')
            .erase()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .save()
            """)

    def test_bad_run_args_with_both_source_and_include(self):
        return
        # TODO: This check was too simple, and broke a few things:
        # https://bitbucket.org/ned/coveragepy/issues/541/coverage-43-breaks-nosetest-with-coverage
        with self.assertRaisesRegex(CoverageException, 'mutually exclusive'):
            self.command_line("run --include=pre1,pre2 --source=lol,wut foo.py", ret=ERR)

    def test_bad_concurrency(self):
        self.command_line("run --concurrency=nothing", ret=ERR)
        out = self.stdout()
        self.assertIn("option --concurrency: invalid choice: 'nothing'", out)

    def test_no_multiple_concurrency(self):
        # You can't use multiple concurrency values on the command line.
        # I would like to have a better message about not allowing multiple
        # values for this option, but optparse is not that flexible.
        self.command_line("run --concurrency=multiprocessing,gevent foo.py", ret=ERR)
        out = self.stdout()
        self.assertIn("option --concurrency: invalid choice: 'multiprocessing,gevent'", out)

    def test_multiprocessing_needs_config_file(self):
        # You can't use command-line args to add options to multiprocessing
        # runs, since they won't make it to the subprocesses. You need to use a
        # config file.
        self.command_line("run --concurrency=multiprocessing --branch foo.py", ret=ERR)
        self.assertIn(
            "Options affecting multiprocessing must be specified in a configuration file.",
            self.stdout()
        )

    def test_run_debug(self):
        self.cmd_executes("run --debug=opt1 foo.py", """\
            .coverage(debug=["opt1"])
            .erase()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .save()
            """)
        self.cmd_executes("run --debug=opt1,opt2 foo.py", """\
            .coverage(debug=["opt1","opt2"])
            .erase()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .save()
            """)

    def test_run_module(self):
        self.cmd_executes("run -m mymodule", """\
            .coverage()
            .erase()
            .start()
            .run_python_module('mymodule', ['mymodule'])
            .stop()
            .save()
            """)
        self.cmd_executes("run -m mymodule -qq arg1 arg2", """\
            .coverage()
            .erase()
            .start()
            .run_python_module('mymodule', ['mymodule', '-qq', 'arg1', 'arg2'])
            .stop()
            .save()
            """)
        self.cmd_executes("run --branch -m mymodule", """\
            .coverage(branch=True)
            .erase()
            .start()
            .run_python_module('mymodule', ['mymodule'])
            .stop()
            .save()
            """)
        self.cmd_executes_same("run -m mymodule", "run --module mymodule")

    def test_run_nothing(self):
        self.command_line("run", ret=ERR)
        self.assertIn("Nothing to do", self.stdout())

    def test_cant_append_parallel(self):
        self.command_line("run --append --parallel-mode foo.py", ret=ERR)
        self.assertIn("Can't append to data files in parallel mode.", self.stdout())

    def test_xml(self):
        # coverage xml [-i] [--omit DIR,...] [FILE1 FILE2 ...]
        self.cmd_executes("xml", """\
            .coverage()
            .load()
            .xml_report()
            """)
        self.cmd_executes("xml -i", """\
            .coverage()
            .load()
            .xml_report(ignore_errors=True)
            """)
        self.cmd_executes("xml -o myxml.foo", """\
            .coverage()
            .load()
            .xml_report(outfile="myxml.foo")
            """)
        self.cmd_executes("xml -o -", """\
            .coverage()
            .load()
            .xml_report(outfile="-")
            """)
        self.cmd_executes("xml --omit fooey", """\
            .coverage(omit=["fooey"])
            .load()
            .xml_report(omit=["fooey"])
            """)
        self.cmd_executes("xml --omit fooey,booey", """\
            .coverage(omit=["fooey", "booey"])
            .load()
            .xml_report(omit=["fooey", "booey"])
            """)
        self.cmd_executes("xml mod1", """\
            .coverage()
            .load()
            .xml_report(morfs=["mod1"])
            """)
        self.cmd_executes("xml mod1 mod2 mod3", """\
            .coverage()
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
        out = self.stdout()
        self.assertIn("fooey", out)
        self.assertIn("help", out)


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
        self.old_CoverageScript = coverage.cmdline.CoverageScript
        coverage.cmdline.CoverageScript = self.CoverageScriptStub
        self.addCleanup(self.cleanup_coverage_script)

    def cleanup_coverage_script(self):
        """Restore CoverageScript when the test is done."""
        coverage.cmdline.CoverageScript = self.old_CoverageScript

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
