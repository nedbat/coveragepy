"""Tests for Coverage.py's improved tokenizer."""

import os, re, sys

sys.path.insert(0, os.path.split(__file__)[0]) # Force relative import for Py3k
from coveragetest import CoverageTest

from coverage.phystokens import source_token_lines


SIMPLE = """\
# yay!
def foo():
  say('two = %d' % 2)
"""

HERE = os.path.split(__file__)[0]

class PhysTokensTest(CoverageTest):
    """Tests for Coverage.py's improver tokenizer."""

    def setUp(self):
        self.run_in_temp_dir = False
        super(PhysTokensTest, self).setUp()

    def check_tokenization(self, source):
        """Tokenize `source`, then put it back together, should be the same."""
        tokenized = ""
        for line in source_token_lines(source):
            text = "".join([t for _,t in line])
            tokenized += text + "\n"
        # source_token_lines doesn't preserve trailing spaces, so trim all that
        # before comparing.
        source = re.sub("(?m)[ \t]+$", "", source)
        tokenized = re.sub("(?m)[ \t]+$", "", tokenized)
        #if source != tokenized:
        #    open("0.py", "w").write(source)
        #    open("1.py", "w").write(tokenized)
        self.assertEqual(source, tokenized)

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
            ]
            )
        self.check_tokenization(SIMPLE)

    def test_tokenize_real_file(self):
        real_file = os.path.join(HERE, "test_coverage.py")
        self.check_file_tokenization(real_file)

    def test_stress(self):
        stress = os.path.join(HERE, "stress_phystoken.txt")
        self.check_file_tokenization(stress)
