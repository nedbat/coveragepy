"""Test cmdline.py for coverage."""

import unittest

import coverage

from coveragetest import CoverageTest


class CmdLineTest(CoverageTest):
    """Tests of command-line processing for coverage.py."""

    def help_fn(self, error=None):
        raise Exception(error or "__doc__")

    def command_line(self, argv):
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


if __name__ == '__main__':
    unittest.main()
