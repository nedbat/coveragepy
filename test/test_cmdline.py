"""Test cmdline.py for coverage."""

import re, shlex, textwrap, unittest
import coverage
from coveragetest import CoverageTest


class CmdLineParserTest(CoverageTest):
    """Tests of command-line processing for Coverage."""

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
        ret_code = coverage.CoverageScript().command_line(argv, self.help_fn)
        self.assertEqual(ret_code, ret)
        self.assertEqual(self.help_out, help_out)

    def testHelp(self):
        self.command_line('-h', help_out="*usage*")
        self.command_line('--help', help_out="*usage*")

    def testUnknownOption(self):
        # TODO: command_line shouldn't throw this exception, it should be in
        # the help_fn.
        self.assertRaisesMsg(Exception, "option -z not recognized",
            self.command_line, '-z')

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
            help_out="You must specify at least one of -e, -x, -c, -r, -a, or -b."
            )

    def testArglessActions(self):
        self.command_line('-e foo bar', ret=1,
            help_out="Unexpected arguments: foo bar"
            )
        self.command_line('-c baz quux', ret=1,
            help_out="Unexpected arguments: baz quux"
            )


class CmdLineActionTest(CoverageTest):
    """Tests of execution paths through the command line interpreter."""
    
    def model_object(self):
        """Return a Mock suitable for use in CoverageScript."""
        import mock
        mk = mock.Mock()
        mk.coverage.return_value = mk
        return mk
        
    def cmd_executes(self, args, code):
        """Assert that the `args` end up executing the sequence in `code`."""
        argv = shlex.split(args)
        m1 = self.model_object()
        
        coverage.CoverageScript(
            _covpkg=m1, _run_python_file=m1.run_python_file
            ).command_line(argv)

        code = textwrap.dedent(code)
        code = re.sub(r"(?m)^\.", "m2.", code)
        m2 = self.model_object()
        code_obj = compile(code, "<code>", "exec")
        eval(code_obj, globals(), { 'm2': m2 })
        self.assertEqual(m1.method_calls, m2.method_calls)
        
    def testExecution(self):
        self.cmd_executes("-x foo.py", """\
            .coverage(cover_pylib=None, data_suffix=False, timid=None)
            .load()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .save()
            """)
        self.cmd_executes("-e -x foo.py", """\
            .coverage(cover_pylib=None, data_suffix=False, timid=None)
            .erase()
            .start()
            .run_python_file('foo.py', ['foo.py'])
            .stop()
            .save()
            """)


if __name__ == '__main__':
    unittest.main()
