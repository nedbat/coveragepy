"""Test cmdline.py for coverage."""

import pprint, re, shlex, sys, textwrap
import mock
import coverage
import coverage.cmdline
from coverage.misc import ExceptionDuringRun

from tests.coveragetest import CoverageTest, OK, ERR


class CmdLineTest(CoverageTest):
    """Tests of execution paths through the command line interpreter."""

    run_in_temp_dir = False

    # Make a dict mapping function names to the default values that cmdline.py
    # uses when calling the function.
    defaults = mock.Mock()
    defaults.coverage(
        cover_pylib=None, data_suffix=None, timid=None, branch=None,
        config_file=True, source=None, include=None, omit=None, debug=None,
    )
    defaults.annotate(
        directory=None, ignore_errors=None, include=None, omit=None, morfs=[],
    )
    defaults.html_report(
        directory=None, ignore_errors=None, include=None, omit=None, morfs=[],
        title=None,
    )
    defaults.report(
        ignore_errors=None, include=None, omit=None, morfs=[],
        show_missing=None,
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
        return mk

    def mock_command_line(self, args):
        """Run `args` through the command line, with a Mock.

        Returns the Mock it used and the status code returned.

        """
        m = self.model_object()
        ret = coverage.CoverageScript(
            _covpkg=m, _run_python_file=m.run_python_file,
            _run_python_module=m.run_python_module, _help_fn=m.help_fn
            ).command_line(shlex.split(args))
        return m, ret

    def cmd_executes(self, args, code, ret=OK):
        """Assert that the `args` end up executing the sequence in `code`."""
        m1, r1 = self.mock_command_line(args)
        self.assertEqual(
            r1, ret, "Wrong status: got %s, wanted %s" % (r1, ret)
        )

        # Remove all indentation, and change ".foo()" to "m2.foo()".
        code = re.sub(r"(?m)^\s+", "", code)
        code = re.sub(r"(?m)^\.", "m2.", code)
        m2 = self.model_object()
        code_obj = compile(code, "<code>", "exec")
        eval(code_obj, globals(), { 'm2': m2 })

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
        self.assertEqual(r, ret,
                "Wrong status: got %s, wanted %s" % (r, ret)
                )
        if help_msg:
            self.assertEqual(m.method_calls[-1],
                ('help_fn', (help_msg,), {})
                )
        else:
            self.assertEqual(m.method_calls[-1],
                ('help_fn', (), {'topic':topic})
                )


class CmdLineTestTest(CmdLineTest):
    """Tests that our CmdLineTest helpers work."""
    def test_assert_same_method_calls(self):
        # All the other tests here use self.cmd_executes_same in successful
        # ways, so here we just check that it fails.
        with self.assertRaises(AssertionError):
            self.cmd_executes_same("-e", "-c")


class ClassicCmdLineTest(CmdLineTest):
    """Tests of the classic coverage.py command line."""

    def test_erase(self):
        # coverage -e
        self.cmd_executes("-e", """\
            .coverage()
            .erase()
            """)
        self.cmd_executes_same("-e", "--erase")

    def test_execute(self):
        # coverage -x [-p] [-L] [--timid] MODULE.py [ARG1 ARG2 ...]

        # -x calls coverage.load first.
        self.cmd_executes("-x foo.py", """\
            .coverage()
            .load()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .save()
            """)
        # -e -x calls coverage.erase first.
        self.cmd_executes("-e -x foo.py", """\
            .coverage()
            .erase()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .save()
            """)
        # --timid sets a flag, and program arguments get passed through.
        self.cmd_executes("-x --timid foo.py abc 123", """\
            .coverage(timid=True)
            .load()
            .start()
            .run_python_file('foo.py', ['foo.py', 'abc', '123'])
            .stop()
            .save()
            """)
        # -L sets a flag, and flags for the program don't confuse us.
        self.cmd_executes("-x -p -L foo.py -a -b", """\
            .coverage(cover_pylib=True, data_suffix=True)
            .load()
            .start()
            .run_python_file('foo.py', ['foo.py', '-a', '-b'])
            .stop()
            .save()
            """)

        # Check that long forms of flags do the same thing as short forms.
        self.cmd_executes_same("-x f.py", "--execute f.py")
        self.cmd_executes_same("-e -x f.py", "--erase --execute f.py")
        self.cmd_executes_same("-x -p f.py", "-x --parallel-mode f.py")
        self.cmd_executes_same("-x -L f.py", "-x --pylib f.py")

    def test_combine(self):
        # coverage -c
        self.cmd_executes("-c", """\
            .coverage()
            .load()
            .combine()
            .save()
            """)
        self.cmd_executes_same("-c", "--combine")

    def test_report(self):
        # coverage -r [-m] [-i] [-o DIR,...] [FILE1 FILE2 ...]
        self.cmd_executes("-r", """\
            .coverage()
            .load()
            .report(show_missing=None)
            """)
        self.cmd_executes("-r -i", """\
            .coverage()
            .load()
            .report(ignore_errors=True)
            """)
        self.cmd_executes("-r -m", """\
            .coverage()
            .load()
            .report(show_missing=True)
            """)
        self.cmd_executes("-r -o fooey", """\
            .coverage(omit=["fooey"])
            .load()
            .report(omit=["fooey"])
            """)
        self.cmd_executes("-r -o fooey,booey", """\
            .coverage(omit=["fooey", "booey"])
            .load()
            .report(omit=["fooey", "booey"])
            """)
        self.cmd_executes("-r mod1", """\
            .coverage()
            .load()
            .report(morfs=["mod1"])
            """)
        self.cmd_executes("-r mod1 mod2 mod3", """\
            .coverage()
            .load()
            .report(morfs=["mod1", "mod2", "mod3"])
            """)

        self.cmd_executes_same("-r", "--report")
        self.cmd_executes_same("-r -i", "-r --ignore-errors")
        self.cmd_executes_same("-r -m", "-r --show-missing")
        self.cmd_executes_same("-r -o f", "-r --omit=f")
        self.cmd_executes_same("-r -o f", "-r --omit f")
        self.cmd_executes_same("-r -o f,b", "-r --omit=f,b")
        self.cmd_executes_same("-r -o f,b", "-r --omit f,b")
        self.cmd_executes_same("-r -of", "-r --omit=f")
        self.cmd_executes_same("-r -of,b", "-r --omit=f,b")

    def test_annotate(self):
        # coverage -a [-d DIR] [-i] [-o DIR,...] [FILE1 FILE2 ...]
        self.cmd_executes("-a", """\
            .coverage()
            .load()
            .annotate()
            """)
        self.cmd_executes("-a -d dir1", """\
            .coverage()
            .load()
            .annotate(directory="dir1")
            """)
        self.cmd_executes("-a -i", """\
            .coverage()
            .load()
            .annotate(ignore_errors=True)
            """)
        self.cmd_executes("-a -o fooey", """\
            .coverage(omit=["fooey"])
            .load()
            .annotate(omit=["fooey"])
            """)
        self.cmd_executes("-a -o fooey,booey", """\
            .coverage(omit=["fooey", "booey"])
            .load()
            .annotate(omit=["fooey", "booey"])
            """)
        self.cmd_executes("-a mod1", """\
            .coverage()
            .load()
            .annotate(morfs=["mod1"])
            """)
        self.cmd_executes("-a mod1 mod2 mod3", """\
            .coverage()
            .load()
            .annotate(morfs=["mod1", "mod2", "mod3"])
            """)

        self.cmd_executes_same("-a", "--annotate")
        self.cmd_executes_same("-a -d d1", "-a --directory=d1")
        self.cmd_executes_same("-a -i", "-a --ignore-errors")
        self.cmd_executes_same("-a -o f", "-a --omit=f")
        self.cmd_executes_same("-a -o f", "-a --omit f")
        self.cmd_executes_same("-a -o f,b", "-a --omit=f,b")
        self.cmd_executes_same("-a -o f,b", "-a --omit f,b")
        self.cmd_executes_same("-a -of", "-a --omit=f")
        self.cmd_executes_same("-a -of,b", "-a --omit=f,b")

    def test_html_report(self):
        # coverage -b -d DIR [-i] [-o DIR,...] [FILE1 FILE2 ...]
        self.cmd_executes("-b", """\
            .coverage()
            .load()
            .html_report()
            """)
        self.cmd_executes("-b -d dir1", """\
            .coverage()
            .load()
            .html_report(directory="dir1")
            """)
        self.cmd_executes("-b -i", """\
            .coverage()
            .load()
            .html_report(ignore_errors=True)
            """)
        self.cmd_executes("-b -o fooey", """\
            .coverage(omit=["fooey"])
            .load()
            .html_report(omit=["fooey"])
            """)
        self.cmd_executes("-b -o fooey,booey", """\
            .coverage(omit=["fooey", "booey"])
            .load()
            .html_report(omit=["fooey", "booey"])
            """)
        self.cmd_executes("-b mod1", """\
            .coverage()
            .load()
            .html_report(morfs=["mod1"])
            """)
        self.cmd_executes("-b mod1 mod2 mod3", """\
            .coverage()
            .load()
            .html_report(morfs=["mod1", "mod2", "mod3"])
            """)

        self.cmd_executes_same("-b", "--html")
        self.cmd_executes_same("-b -d d1", "-b --directory=d1")
        self.cmd_executes_same("-b -i", "-b --ignore-errors")
        self.cmd_executes_same("-b -o f", "-b --omit=f")
        self.cmd_executes_same("-b -o f,b", "-b --omit=f,b")
        self.cmd_executes_same("-b -of", "-b --omit=f")
        self.cmd_executes_same("-b -of,b", "-b --omit=f,b")

    def test_help(self):
        # coverage -h
        self.cmd_help("-h", topic="help", ret=OK)
        self.cmd_help("--help", topic="help", ret=OK)

    def test_version(self):
        # coverage --version
        self.cmd_help("--version", topic="version", ret=OK)

    ## Error cases

    def test_argless_actions(self):
        self.cmd_help("-e foo bar", "Unexpected arguments: foo bar")
        self.cmd_help("-c baz quux", "Unexpected arguments: baz quux")

    def test_need_action(self):
        self.cmd_help("-p", "You must specify at least one of "
                                                "-e, -x, -c, -r, -a, or -b.")

    def test_bad_action_combinations(self):
        self.cmd_help('-e -a',
            "You can't specify the 'erase' and 'annotate' "
                "options at the same time."
            )
        self.cmd_help('-e -r',
            "You can't specify the 'erase' and 'report' "
                "options at the same time."
            )
        self.cmd_help('-e -b',
            "You can't specify the 'erase' and 'html' "
                "options at the same time."
            )
        self.cmd_help('-e -c',
            "You can't specify the 'erase' and 'combine' "
                "options at the same time."
            )
        self.cmd_help('-x -a',
            "You can't specify the 'execute' and 'annotate' "
                "options at the same time."
            )
        self.cmd_help('-x -r',
            "You can't specify the 'execute' and 'report' "
                "options at the same time."
            )
        self.cmd_help('-x -b',
            "You can't specify the 'execute' and 'html' "
                "options at the same time."
            )
        self.cmd_help('-x -c',
            "You can't specify the 'execute' and 'combine' "
                "options at the same time."
            )

    def test_nothing_to_do(self):
        self.cmd_help("-x", "Nothing to do.")

    def test_unknown_option(self):
        self.cmd_help("-z", "no such option: -z")


class FakeCoverageForDebugData(object):
    """Just enough of a fake coverage package for the 'debug data' tests."""
    def __init__(self, summary):
        self._summary = summary
        self.filename = "FILENAME"
        self.data = self

    # package members
    def coverage(self, *unused_args, **unused_kwargs):
        """The coverage class in the package."""
        return self

    # coverage methods
    def load(self):
        """Fake coverage().load()"""
        pass

    # data methods
    def has_arcs(self):
        """Fake coverage().data.has_arcs()"""
        return False

    def summary(self, fullpath):                    # pylint: disable=W0613
        """Fake coverage().data.summary()"""
        return self._summary


class NewCmdLineTest(CmdLineTest):
    """Tests of the coverage.py command line."""

    def test_annotate(self):
        self.cmd_executes_same("annotate", "-a")
        self.cmd_executes_same("annotate -i", "-a -i")
        self.cmd_executes_same("annotate -d d1", "-a -d d1")
        self.cmd_executes_same("annotate --omit f", "-a --omit f")
        self.cmd_executes_same("annotate --omit f,b", "-a --omit f,b")
        self.cmd_executes_same("annotate m1", "-a m1")
        self.cmd_executes_same("annotate m1 m2 m3", "-a m1 m2 m3")

    def test_combine(self):
        self.cmd_executes_same("combine", "-c")

    def test_debug(self):
        self.cmd_help("debug", "What information would you like: data, sys?")
        self.cmd_help("debug foo", "Don't know what you mean by 'foo'")

    def test_debug_data(self):
        fake = FakeCoverageForDebugData({
            'file1.py': 17, 'file2.py': 23,
            })
        self.command_line("debug data", _covpkg=fake)
        self.assertMultiLineEqual(self.stdout(), textwrap.dedent("""\
            -- data ---------------------------------------
            path: FILENAME
            has_arcs: False

            2 files:
            file1.py: 17 lines
            file2.py: 23 lines
            """))

    def test_debug_data_with_no_data(self):
        fake = FakeCoverageForDebugData({})
        self.command_line("debug data", _covpkg=fake)
        self.assertMultiLineEqual(self.stdout(), textwrap.dedent("""\
            -- data ---------------------------------------
            path: FILENAME
            has_arcs: False
            No data collected
            """))

    def test_debug_sys(self):
        self.command_line("debug sys")
        out = self.stdout()
        assert "version:" in out
        assert "data_path:" in out

    def test_erase(self):
        self.cmd_executes_same("erase", "-e")

    def test_help(self):
        self.cmd_executes("help", ".help_fn(topic='help')")

    def test_cmd_help(self):
        self.cmd_executes("run --help",
                                ".help_fn(parser='<CmdOptionParser:run>')")
        self.cmd_executes_same("help run", "run --help")

    def test_html(self):
        self.cmd_executes_same("html", "-b")
        self.cmd_executes_same("html -i", "-b -i")
        self.cmd_executes_same("html -d d1", "-b -d d1")
        self.cmd_executes_same("html --omit f", "-b --omit f")
        self.cmd_executes_same("html --omit f,b", "-b --omit f,b")
        self.cmd_executes_same("html m1", "-b m1")
        self.cmd_executes_same("html m1 m2 m3", "-b m1 m2 m3")
        self.cmd_executes("html", """\
            .coverage()
            .load()
            .html_report()
            """)
        self.cmd_executes("html --title=Hello_there", """\
            .coverage()
            .load()
            .html_report(title='Hello_there')
            """)

    def test_report(self):
        self.cmd_executes_same("report", "-r")
        self.cmd_executes_same("report -i", "-r -i")
        self.cmd_executes_same("report -m", "-r -m")
        self.cmd_executes_same("report --omit f", "-r --omit f")
        self.cmd_executes_same("report --omit f,b", "-r --omit f,b")
        self.cmd_executes_same("report m1", "-r m1")
        self.cmd_executes_same("report m1 m2 m3", "-r m1 m2 m3")

    def test_run(self):
        self.cmd_executes_same("run f.py", "-e -x f.py")
        self.cmd_executes_same("run f.py -a arg -z", "-e -x f.py -a arg -z")
        self.cmd_executes_same("run -a f.py", "-x f.py")
        self.cmd_executes_same("run -p f.py", "-e -x -p f.py")
        self.cmd_executes_same("run -L f.py", "-e -x -L f.py")
        self.cmd_executes_same("run --timid f.py", "-e -x --timid f.py")
        self.cmd_executes_same("run", "-x")
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
        self.cmd_executes("run --include=pre1,pre2 --omit=opre1,opre2 foo.py",
            """\
            .coverage(include=["pre1", "pre2"], omit=["opre1", "opre2"])
            .erase()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .save()
            """)
        self.cmd_executes("run --source=quux,hi.there,/home/bar foo.py",
            """\
            .coverage(source=["quux", "hi.there", "/home/bar"])
            .erase()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .save()
            """)

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


class CmdLineStdoutTest(CmdLineTest):
    """Test the command line with real stdout output."""

    def test_minimum_help(self):
        self.command_line("")
        out = self.stdout()
        assert "Code coverage for Python." in out
        assert out.count("\n") < 4

    def test_version(self):
        self.command_line("--version")
        out = self.stdout()
        assert "ersion " in out
        assert out.count("\n") < 4

    def test_help(self):
        self.command_line("help")
        out = self.stdout()
        assert "nedbatchelder.com" in out
        assert out.count("\n") > 10

    def test_cmd_help(self):
        self.command_line("help run")
        out = self.stdout()
        assert "<pyfile>" in out
        assert "--timid" in out
        assert out.count("\n") > 10

    def test_error(self):
        self.command_line("fooey kablooey", ret=ERR)
        out = self.stdout()
        assert "fooey" in out
        assert "help" in out


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
                raise AssertionError("Bad CoverageScriptStub: %r"% (argv,))
            return 0

    def setUp(self):
        super(CmdMainTest, self).setUp()
        self.old_CoverageScript = coverage.cmdline.CoverageScript
        coverage.cmdline.CoverageScript = self.CoverageScriptStub

    def tearDown(self):
        coverage.cmdline.CoverageScript = self.old_CoverageScript
        super(CmdMainTest, self).tearDown()

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
        with self.assertRaisesRegexp(ValueError, "coverage is broken"):
            coverage.cmdline.main(['internalraise'])

    def test_exit(self):
        ret = coverage.cmdline.main(['exit'])
        self.assertEqual(ret, 23)
