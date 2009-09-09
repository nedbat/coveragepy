"""Test cmdline.py for coverage."""

import re, shlex, textwrap, unittest
import coverage
from coveragetest import CoverageTest


class CmdLineParserTest(CoverageTest):
    """Tests of command-line processing for Coverage."""

    def help_fn(self, error=None):
        """A mock help_fn to capture the error messages for tests."""
        raise Exception(error or "__doc__")

    def command_line(self, argv):
        """Run a Coverage command line, with `argv` as arguments."""
        return coverage.CoverageScript().command_line(argv, self.help_fn)

    def testHelp(self):
        self.assertRaisesMsg(Exception, "__doc__", self.command_line, ['-h'])
        self.assertRaisesMsg(Exception, "__doc__", self.command_line,
            ['--help'])

    def testUnknownOption(self):
        self.assertRaisesMsg(Exception, "option -z not recognized",
            self.command_line, ['-z'])

    def testBadActionCombinations(self):
        self.assertRaisesMsg(Exception,
            "You can't specify the 'erase' and 'annotate' "
            "options at the same time.", self.command_line, ['-e', '-a'])
        self.assertRaisesMsg(Exception,
            "You can't specify the 'erase' and 'report' "
            "options at the same time.", self.command_line, ['-e', '-r'])
        self.assertRaisesMsg(Exception,
            "You can't specify the 'erase' and 'html' "
            "options at the same time.", self.command_line, ['-e', '-b'])
        self.assertRaisesMsg(Exception,
            "You can't specify the 'erase' and 'combine' "
            "options at the same time.", self.command_line, ['-e', '-c'])
        self.assertRaisesMsg(Exception,
            "You can't specify the 'execute' and 'annotate' "
            "options at the same time.", self.command_line, ['-x', '-a'])
        self.assertRaisesMsg(Exception,
            "You can't specify the 'execute' and 'report' "
            "options at the same time.", self.command_line, ['-x', '-r'])
        self.assertRaisesMsg(Exception,
            "You can't specify the 'execute' and 'html' "
            "options at the same time.", self.command_line, ['-x', '-b'])
        self.assertRaisesMsg(Exception,
            "You can't specify the 'execute' and 'combine' "
            "options at the same time.", self.command_line, ['-x', '-c'])

    def testNeedAction(self):
        self.assertRaisesMsg(Exception,
            "You must specify at least one of -e, -x, -c, -r, -a, or -b.",
            self.command_line, ['-p'])

    def testArglessActions(self):
        self.assertRaisesMsg(Exception, "Unexpected arguments: foo bar",
            self.command_line, ['-e', 'foo', 'bar'])
        self.assertRaisesMsg(Exception, "Unexpected arguments: baz quux",
            self.command_line, ['-c', 'baz', 'quux'])


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
