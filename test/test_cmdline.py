"""Test cmdline.py for coverage."""

import re, shlex, textwrap, unittest
import mock
import coverage
from coveragetest import CoverageTest


class CmdLineParserTest(CoverageTest):
    """Tests of command-line processing for Coverage."""

    def setUp(self):
        super(CmdLineParserTest, self).setUp()
        self.help_out = None

    def help_fn(self, error=None):
        """A mock help_fn to capture the error messages for tests."""
        self.help_out = error or "*usage*"

    def command_line(self, args, ret=0, help_out=""):
        """Run a Coverage command line, with `args` as arguments.
        
        The return code must be `ret`, and the help messages written must be
        `help_out`.
        
        """
        self.help_out = ""
        argv = shlex.split(args)
        ret_code = coverage.CoverageScript(_help_fn=self.help_fn).command_line(argv)
        self.assertEqual(ret_code, ret)
        self.assertEqual(self.help_out, help_out)

    def testHelp(self):
        self.command_line('-h', help_out="*usage*")
        self.command_line('--help', help_out="*usage*")

    def testUnknownOption(self):
        self.command_line('-z', ret=1,
            help_out="no such option: -z"
            )

    def testBadActionCombinations(self):
        self.command_line('-e -a', ret=1,
            help_out="You can't specify the 'erase' and 'annotate' "
                "options at the same time."
            )
        self.command_line('-e -r', ret=1,
            help_out="You can't specify the 'erase' and 'report' "
                "options at the same time."
            )
        self.command_line('-e -b', ret=1,
            help_out="You can't specify the 'erase' and 'html' "
                "options at the same time."
            )
        self.command_line('-e -c', ret=1,
            help_out="You can't specify the 'erase' and 'combine' "
                "options at the same time."
            )
        self.command_line('-x -a', ret=1,
            help_out="You can't specify the 'execute' and 'annotate' "
                "options at the same time."
            )
        self.command_line('-x -r', ret=1,
            help_out="You can't specify the 'execute' and 'report' "
                "options at the same time."
            )
        self.command_line('-x -b', ret=1,
            help_out="You can't specify the 'execute' and 'html' "
                "options at the same time."
            )
        self.command_line('-x -c', ret=1,
            help_out="You can't specify the 'execute' and 'combine' "
                "options at the same time."
            )

    def testNeedAction(self):
        self.command_line('-p', ret=1,
            help_out="You must specify at least one of "
                                                "-e, -x, -c, -r, -a, or -b."
            )

    def testArglessActions(self):
        self.command_line('-e foo bar', ret=1,
            help_out="Unexpected arguments: foo bar"
            )
        self.command_line('-c baz quux', ret=1,
            help_out="Unexpected arguments: baz quux"
            )

    def testNothingToDo(self):
        self.command_line('-x', ret=1,
            help_out="Nothing to do."
            )


class CmdLineActionTest(CoverageTest):
    """Tests of execution paths through the command line interpreter."""
    
    def model_object(self):
        """Return a Mock suitable for use in CoverageScript."""
        mk = mock.Mock()
        mk.coverage.return_value = mk
        return mk

    def run_command_line(self, args):
        """Run `args` through command_line, returning the Mock it used."""
        m = self.model_object()
        coverage.CoverageScript(
            _covpkg=m, _run_python_file=m.run_python_file
            ).command_line(shlex.split(args))
        return m
    
    def cmd_executes(self, args, code):
        """Assert that the `args` end up executing the sequence in `code`."""
        m1 = self.run_command_line(args)

        code = textwrap.dedent(code)
        code = re.sub(r"(?m)^\.", "m2.", code)
        m2 = self.model_object()
        code_obj = compile(code, "<code>", "exec")
        eval(code_obj, globals(), { 'm2': m2 })
        self.assertEqual(m1.method_calls, m2.method_calls)
        
    def cmd_executes_same(self, args1, args2):
        """Assert that the `args1` executes the same as `args2`."""
        m1 = self.run_command_line(args1)
        m2 = self.run_command_line(args2)
        self.assertEqual(m1.method_calls, m2.method_calls)
        
    def testErase(self):
        # coverage -e
        self.cmd_executes("-e", """\
            .coverage(cover_pylib=None, data_suffix=False, timid=None)
            .erase()
            """)
        self.cmd_executes_same("-e", "--erase")

    def testExecute(self):
        # coverage -x [-p] [-L] [--timid] MODULE.py [ARG1 ARG2 ...]
        
        # -x calls coverage.load first.
        self.cmd_executes("-x foo.py", """\
            .coverage(cover_pylib=None, data_suffix=False, timid=None)
            .load()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .save()
            """)
        # -e -x calls coverage.erase first.
        self.cmd_executes("-e -x foo.py", """\
            .coverage(cover_pylib=None, data_suffix=False, timid=None)
            .erase()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .save()
            """)
        # --timid sets a flag, and program arguments get passed through.
        self.cmd_executes("-x --timid foo.py abc 123", """\
            .coverage(cover_pylib=None, data_suffix=False, timid=True)
            .load()
            .start()
            .run_python_file('foo.py', ['foo.py', 'abc', '123'])
            .stop()
            .save()
            """)
        # -L sets a flag, and flags for the program don't confuse us.
        self.cmd_executes("-x -p -L foo.py -a -b", """\
            .coverage(cover_pylib=True, data_suffix=True, timid=None)
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

    def testCombine(self):
        # coverage -c
        self.cmd_executes("-c", """\
            .coverage(cover_pylib=None, data_suffix=False, timid=None)
            .load()
            .combine()
            .save()
            """)
        self.cmd_executes_same("-c", "--combine")

    def testReport(self):
        # coverage -r [-m] [-i] [-o DIR,...] [FILE1 FILE2 ...]

        init_load = """\
            .coverage(cover_pylib=None, data_suffix=False, timid=None)
            .load()\n"""
            
        self.cmd_executes("-r", init_load + """\
            .report(ignore_errors=None, omit_prefixes=None, morfs=[],
                    show_missing=None)
            """)
        self.cmd_executes("-r -i", init_load + """\
            .report(ignore_errors=True, omit_prefixes=None, morfs=[],
                    show_missing=None)
            """)
        self.cmd_executes("-r -m", init_load + """\
            .report(ignore_errors=None, omit_prefixes=None, morfs=[],
                    show_missing=True)
            """)
        self.cmd_executes("-r -o fooey", init_load + """\
            .report(ignore_errors=None, omit_prefixes=["fooey"],
                    morfs=[], show_missing=None)
            """)
        self.cmd_executes("-r -o fooey,booey", init_load + """\
            .report(ignore_errors=None, omit_prefixes=["fooey", "booey"],
                    morfs=[], show_missing=None)
            """)
        self.cmd_executes("-r mod1", init_load + """\
            .report(ignore_errors=None, omit_prefixes=None,
                    morfs=["mod1"], show_missing=None)
            """)
        self.cmd_executes("-r mod1 mod2 mod3", init_load + """\
            .report(ignore_errors=None, omit_prefixes=None,
                    morfs=["mod1", "mod2", "mod3"], show_missing=None)
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

    def testAnnotate(self):
        # coverage -a [-d DIR] [-i] [-o DIR,...] [FILE1 FILE2 ...]
        init_load = """\
            .coverage(cover_pylib=None, data_suffix=False, timid=None)
            .load()\n"""
            
        self.cmd_executes("-a", init_load + """\
            .annotate(directory=None, ignore_errors=None,
                    omit_prefixes=None, morfs=[])
            """)
        self.cmd_executes("-a -d dir1", init_load + """\
            .annotate(directory="dir1", ignore_errors=None,
                    omit_prefixes=None, morfs=[])
            """)
        self.cmd_executes("-a -i", init_load + """\
            .annotate(directory=None, ignore_errors=True,
                    omit_prefixes=None, morfs=[])
            """)
        self.cmd_executes("-a -o fooey", init_load + """\
            .annotate(directory=None, ignore_errors=None,
                    omit_prefixes=["fooey"], morfs=[])
            """)
        self.cmd_executes("-a -o fooey,booey", init_load + """\
            .annotate(directory=None, ignore_errors=None,
                    omit_prefixes=["fooey", "booey"], morfs=[])
            """)
        self.cmd_executes("-a mod1", init_load + """\
            .annotate(directory=None, ignore_errors=None,
                    omit_prefixes=None, morfs=["mod1"])
            """)
        self.cmd_executes("-a mod1 mod2 mod3", init_load + """\
            .annotate(directory=None, ignore_errors=None,
                    omit_prefixes=None, morfs=["mod1", "mod2", "mod3"])
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

    def testHtmlReport(self):
        # coverage -b -d DIR [-i] [-o DIR,...] [FILE1 FILE2 ...]
        init_load = """\
            .coverage(cover_pylib=None, data_suffix=False, timid=None)
            .load()\n"""
            
        self.cmd_executes("-b", init_load + """\
            .html_report(directory=None, ignore_errors=None,
                    omit_prefixes=None, morfs=[])
            """)
        self.cmd_executes("-b -d dir1", init_load + """\
            .html_report(directory="dir1", ignore_errors=None,
                    omit_prefixes=None, morfs=[])
            """)
        self.cmd_executes("-b -i", init_load + """\
            .html_report(directory=None, ignore_errors=True,
                    omit_prefixes=None, morfs=[])
            """)
        self.cmd_executes("-b -o fooey", init_load + """\
            .html_report(directory=None, ignore_errors=None,
                    omit_prefixes=["fooey"], morfs=[])
            """)
        self.cmd_executes("-b -o fooey,booey", init_load + """\
            .html_report(directory=None, ignore_errors=None,
                    omit_prefixes=["fooey", "booey"], morfs=[])
            """)
        self.cmd_executes("-b mod1", init_load + """\
            .html_report(directory=None, ignore_errors=None,
                    omit_prefixes=None, morfs=["mod1"])
            """)
        self.cmd_executes("-b mod1 mod2 mod3", init_load + """\
            .html_report(directory=None, ignore_errors=None,
                    omit_prefixes=None, morfs=["mod1", "mod2", "mod3"])
            """)

        self.cmd_executes_same("-b", "--html")
        self.cmd_executes_same("-b -d d1", "-b --directory=d1")
        self.cmd_executes_same("-b -i", "-b --ignore-errors")
        self.cmd_executes_same("-b -o f", "-b --omit=f")
        self.cmd_executes_same("-b -o f,b", "-b --omit=f,b")
        self.cmd_executes_same("-b -of", "-b --omit=f")
        self.cmd_executes_same("-b -of,b", "-b --omit=f,b")


if __name__ == '__main__':
    unittest.main()
