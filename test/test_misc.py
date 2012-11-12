"""Tests of miscellaneous stuff."""

import os, sys

from coverage.misc import Hasher
from coverage import __version__, __url__
sys.path.insert(0, os.path.split(__file__)[0]) # Force relative import for Py3k
from coveragetest import CoverageTest

class HasherTest(CoverageTest):
    """Test our wrapper of md5 hashing."""

    def test_string_hashing(self):
        h1 = Hasher()
        h1.update("Hello, world!")
        h2 = Hasher()
        h2.update("Goodbye!")
        h3 = Hasher()
        h3.update("Hello, world!")
        self.assertNotEqual(h1.digest(), h2.digest())
        self.assertEqual(h1.digest(), h3.digest())

    def test_dict_hashing(self):
        h1 = Hasher()
        h1.update({'a': 17, 'b': 23})
        h2 = Hasher()
        h2.update({'b': 23, 'a': 17})
        self.assertEqual(h1.digest(), h2.digest())


class SetupPyTest(CoverageTest):
    """Tests of setup.py"""

    run_in_temp_dir = False

    def test_version(self):
        status, output = self.run_command_status(
            "python setup.py --description --version --url --author"
            )
        self.assertEqual(status, 0)
        out = output.splitlines()
        self.assertIn("measurement", out[0])
        self.assertEqual(out[1], __version__)
        self.assertEqual(out[2], __url__)
        self.assertIn("Ned Batchelder", out[3])
