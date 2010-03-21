"""Tests for files.py"""

import os, sys

from coverage.files import FileLocator

sys.path.insert(0, os.path.split(__file__)[0]) # Force relative import for Py3k
from coveragetest import CoverageTest


class FileLocatorTest(CoverageTest):
    """Tests of `FileLocator`."""

    def abs_path(self, p):
        """Return the absolute path for `p`."""
        return os.path.join(os.getcwd(), os.path.normpath(p))

    def test_simple(self):
        self.make_file("hello.py", "#hello")
        fl = FileLocator()
        self.assertEqual(fl.relative_filename("hello.py"), "hello.py")
        a = self.abs_path("hello.py")
        self.assertNotEqual(a, "hello.py")
        self.assertEqual(fl.relative_filename(a), "hello.py")

    def test_peer_directories(self):
        self.make_file("sub/proj1/file1.py", "file1")
        self.make_file("sub/proj2/file2.py", "file2")
        a1 = self.abs_path("sub/proj1/file1.py")
        a2 = self.abs_path("sub/proj2/file2.py")
        d = os.path.normpath("sub/proj1")
        os.chdir(d)
        fl = FileLocator()
        self.assertEqual(fl.relative_filename(a1), "file1.py")
        self.assertEqual(fl.relative_filename(a2), a2)
