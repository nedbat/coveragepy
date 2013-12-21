"""Tests for Coverage.py's improved tokenizer."""

import os, re, sys
from tests.coveragetest import CoverageTest
from coverage.phystokens import source_token_lines, source_encoding


SIMPLE = """\
# yay!
def foo():
  say('two = %d' % 2)
"""

MIXED_WS = """\
def hello():
        a="Hello world!"
\tb="indented"
"""

HERE = os.path.split(__file__)[0]


class PhysTokensTest(CoverageTest):
    """Tests for Coverage.py's improver tokenizer."""

    run_in_temp_dir = False

    def check_tokenization(self, source):
        """Tokenize `source`, then put it back together, should be the same."""
        tokenized = ""
        for line in source_token_lines(source):
            text = "".join(t for _, t in line)
            tokenized += text + "\n"
        # source_token_lines doesn't preserve trailing spaces, so trim all that
        # before comparing.
        source = source.replace('\r\n', '\n')
        source = re.sub(r"(?m)[ \t]+$", "", source)
        tokenized = re.sub(r"(?m)[ \t]+$", "", tokenized)
        self.assertMultiLineEqual(source, tokenized)

    def check_file_tokenization(self, fname):
        """Use the contents of `fname` for `check_tokenization`."""
        self.check_tokenization(open(fname).read())

    def test_simple(self):
        self.assertEqual(list(source_token_lines(SIMPLE)),
            [
                [('com', "# yay!")],
                [('key', 'def'), ('ws', ' '), ('nam', 'foo'), ('op', '('),
                            ('op', ')'), ('op', ':')],
                [('ws', '  '), ('nam', 'say'), ('op', '('),
                            ('str', "'two = %d'"), ('ws', ' '), ('op', '%'),
                            ('ws', ' '), ('num', '2'), ('op', ')')]
            ])
        self.check_tokenization(SIMPLE)

    def test_tab_indentation(self):
        # Mixed tabs and spaces...
        self.assertEqual(list(source_token_lines(MIXED_WS)),
            [
                [('key', 'def'), ('ws', ' '), ('nam', 'hello'), ('op', '('),
                            ('op', ')'), ('op', ':')],
                [('ws', '        '), ('nam', 'a'), ('op', '='),
                            ('str', '"Hello world!"')],
                [('ws', '        '), ('nam', 'b'), ('op', '='),
                            ('str', '"indented"')],
            ])

    def test_tokenize_real_file(self):
        # Check the tokenization of a real file (large, btw).
        real_file = os.path.join(HERE, "test_coverage.py")
        self.check_file_tokenization(real_file)

    def test_stress(self):
        # Check the tokenization of a stress-test file.
        stress = os.path.join(HERE, "stress_phystoken.tok")
        self.check_file_tokenization(stress)
        stress = os.path.join(HERE, "stress_phystoken_dos.tok")
        self.check_file_tokenization(stress)


# source_encoding is only used on Py2.
if sys.version_info < (3, 0):
    class SourceEncodingTest(CoverageTest):
        """Tests of source_encoding() for detecting encodings on Py2."""

        run_in_temp_dir = False

        def test_detect_source_encoding(self):
            # Various forms from http://www.python.org/dev/peps/pep-0263/
            source = "# coding=cp850\n\n"
            self.assertEqual(source_encoding(source), 'cp850')
            source = "#!/usr/bin/python\n# -*- coding: utf-8 -*-\n"
            self.assertEqual(source_encoding(source), 'utf-8')
            source = "#!/usr/bin/python\n# vim: set fileencoding=utf8 :\n"
            self.assertEqual(source_encoding(source), 'utf8')
            source = "# This Python file uses this encoding: utf-8\n"
            self.assertEqual(source_encoding(source), 'utf-8')

        def test_detect_source_encoding_on_second_line(self):
            # A coding declaration should be found despite a first blank line.
            source = "\n# coding=cp850\n\n"
            self.assertEqual(source_encoding(source), 'cp850')

        def test_dont_detect_source_encoding_on_third_line(self):
            # A coding declaration doesn't count on the third line.
            source = "\n\n# coding=cp850\n\n"
            self.assertEqual(source_encoding(source), 'ascii')

        def test_detect_source_encoding_of_empty_file(self):
            # An important edge case.
            self.assertEqual(source_encoding(""), 'ascii')

        def test_bom(self):
            # A BOM means utf-8.
            source = "\xEF\xBB\xBFtext = 'hello'\n"
            self.assertEqual(source_encoding(source), 'utf-8-sig')

            # But it has to be the only authority.
            source = "\xEF\xBB\xBF# coding: cp850\n"
            with self.assertRaises(SyntaxError):
                source_encoding(source)
