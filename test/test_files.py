"""Tests for files.py"""

import os, sys

from coverage.files import FileLocator, TreeMatcher, FnmatchMatcher
from coverage.files import find_python_files
from coverage.backward import set                   # pylint: disable=W0622

sys.path.insert(0, os.path.split(__file__)[0]) # Force relative import for Py3k
from coveragetest import CoverageTest


class FileLocatorTest(CoverageTest):
    """Tests of `FileLocator`."""

    def abs_path(self, p):
        """Return the absolute path for `p`."""
        return os.path.join(os.getcwd(), os.path.normpath(p))

    def test_simple(self):
        self.make_file("hello.py")
        fl = FileLocator()
        self.assertEqual(fl.relative_filename("hello.py"), "hello.py")
        a = self.abs_path("hello.py")
        self.assertNotEqual(a, "hello.py")
        self.assertEqual(fl.relative_filename(a), "hello.py")

    def test_peer_directories(self):
        self.make_file("sub/proj1/file1.py")
        self.make_file("sub/proj2/file2.py")
        a1 = self.abs_path("sub/proj1/file1.py")
        a2 = self.abs_path("sub/proj2/file2.py")
        d = os.path.normpath("sub/proj1")
        os.chdir(d)
        fl = FileLocator()
        self.assertEqual(fl.relative_filename(a1), "file1.py")
        self.assertEqual(fl.relative_filename(a2), a2)


class MatcherTest(CoverageTest):
    """Tests of file matchers."""

    def test_tree_matcher(self):
        file1 = self.make_file("sub/file1.py")
        file2 = self.make_file("sub/file2.c")
        file3 = self.make_file("sub2/file3.h")
        file4 = self.make_file("sub3/file4.py")
        file5 = self.make_file("sub3/file5.c")
        fl = FileLocator()
        tm = TreeMatcher([
            fl.canonical_filename("sub"),
            fl.canonical_filename(file4),
            ])
        self.assertTrue(tm.match(fl.canonical_filename(file1)))
        self.assertTrue(tm.match(fl.canonical_filename(file2)))
        self.assertFalse(tm.match(fl.canonical_filename(file3)))
        self.assertTrue(tm.match(fl.canonical_filename(file4)))
        self.assertFalse(tm.match(fl.canonical_filename(file5)))

    def test_fnmatch_matcher(self):
        file1 = self.make_file("sub/file1.py")
        file2 = self.make_file("sub/file2.c")
        file3 = self.make_file("sub2/file3.h")
        file4 = self.make_file("sub3/file4.py")
        file5 = self.make_file("sub3/file5.c")
        fl = FileLocator()
        fnm = FnmatchMatcher(["*.py", "*/sub2/*"])
        self.assertTrue(fnm.match(fl.canonical_filename(file1)))
        self.assertFalse(fnm.match(fl.canonical_filename(file2)))
        self.assertTrue(fnm.match(fl.canonical_filename(file3)))
        self.assertTrue(fnm.match(fl.canonical_filename(file4)))
        self.assertFalse(fnm.match(fl.canonical_filename(file5)))


class FindPythonFilesTest(CoverageTest):
    """Tests of `find_python_files`."""

    def test_find_python_files(self):
        self.make_file("sub/a.py")
        self.make_file("sub/b.py")
        self.make_file("sub/__init__.py")
        self.make_file("sub/x.c")                   # nope: not .py
        self.make_file("sub/ssub/__init__.py")
        self.make_file("sub/ssub/s.py")
        self.make_file("sub/lab/exp.py")            # nope: no __init__.py
        py_files = set(find_python_files("sub"))
        self.assert_same_files(py_files, [
            "sub/__init__.py", "sub/a.py", "sub/b.py",
            "sub/ssub/__init__.py", "sub/ssub/s.py",
            ])

