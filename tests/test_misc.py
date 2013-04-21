"""Tests of miscellaneous stuff."""
import sys

from coverage.misc import Hasher, file_be_gone
from coverage import __version__, __url__
from tests.coveragetest import CoverageTest

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


class RemoveFileTest(CoverageTest):
    """Tests of misc.file_be_gone."""

    def test_remove_nonexistent_file(self):
        # it's ok to try to remove a file that doesn't exist.
        file_be_gone("not_here.txt")

    def test_remove_actual_file(self):
        # it really does remove a file that does exist.
        self.make_file("here.txt", "We are here, we are here, we are here!")
        file_be_gone("here.txt")
        self.assert_doesnt_exist("here.txt")

    def test_actual_errors(self):
        # Errors can still happen.
        # ". is a directory" on Unix, or "Access denied" on Windows
        self.assertRaises(OSError, file_be_gone, ".")


class SetupPyTest(CoverageTest):
    """Tests of setup.py"""

    run_in_temp_dir = False

    def test_metadata(self):
        status, output = self.run_command_status(
            "python setup.py --description --version --url --author"
            )
        self.assertEqual(status, 0)
        out = output.splitlines()
        self.assertIn("measurement", out[0])
        self.assertEqual(out[1], __version__)
        self.assertEqual(out[2], __url__)
        self.assertIn("Ned Batchelder", out[3])

    def test_more_metadata(self):
        # Let's be sure we pick up our own setup.py
        # CoverageTest.tearDown restores the original sys.path.
        sys.path.insert(0, '')
        from setup import setup_args

        classifiers = setup_args['classifiers']
        self.assertGreater(len(classifiers), 7)
        self.assertTrue(classifiers[-1].startswith("Development Status ::"))

        long_description = setup_args['long_description'].splitlines()
        self.assertGreater(len(long_description), 7)
        self.assertNotEqual(long_description[0].strip(), "")
        self.assertNotEqual(long_description[-1].strip(), "")
