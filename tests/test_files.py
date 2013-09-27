"""Tests for files.py"""

import os, os.path

from coverage.files import FileLocator, TreeMatcher, FnmatchMatcher
from coverage.files import PathAliases, find_python_files, abs_file
from coverage.backward import set                   # pylint: disable=W0622
from coverage.misc import CoverageException

from tests.coveragetest import CoverageTest


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

    def test_filepath_contains_absolute_prefix_twice(self):
        # https://bitbucket.org/ned/coveragepy/issue/194
        # Build a path that has two pieces matching the absolute path prefix.
        # Technically, this test doesn't do that on Windows, but drive
        # letters make that impractical to acheive.
        fl = FileLocator()
        d = abs_file(os.curdir)
        trick = os.path.splitdrive(d)[1].lstrip(os.path.sep)
        rel = os.path.join('sub', trick, 'file1.py')
        self.assertEqual(fl.relative_filename(abs_file(rel)), rel)


class MatcherTest(CoverageTest):
    """Tests of file matchers."""

    def test_tree_matcher(self):
        file1 = self.make_file("sub/file1.py")
        file2 = self.make_file("sub/file2.c")
        file3 = self.make_file("sub2/file3.h")
        file4 = self.make_file("sub3/file4.py")
        file5 = self.make_file("sub3/file5.c")
        fl = FileLocator()
        trees = [
            fl.canonical_filename("sub"),
            fl.canonical_filename(file4),
            ]
        tm = TreeMatcher(trees)
        self.assertTrue(tm.match(fl.canonical_filename(file1)))
        self.assertTrue(tm.match(fl.canonical_filename(file2)))
        self.assertFalse(tm.match(fl.canonical_filename(file3)))
        self.assertTrue(tm.match(fl.canonical_filename(file4)))
        self.assertFalse(tm.match(fl.canonical_filename(file5)))

        self.assertEqual(tm.info(), trees)

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

        self.assertEqual(fnm.info(), ["*.py", "*/sub2/*"])


class PathAliasesTest(CoverageTest):
    """Tests for coverage/files.py:PathAliases"""

    run_in_temp_dir = False

    def test_noop(self):
        aliases = PathAliases()
        self.assertEqual(aliases.map('/ned/home/a.py'), '/ned/home/a.py')

    def test_nomatch(self):
        aliases = PathAliases()
        aliases.add('/home/*/src', './mysrc')
        self.assertEqual(aliases.map('/home/foo/a.py'), '/home/foo/a.py')

    def test_wildcard(self):
        aliases = PathAliases()
        aliases.add('/ned/home/*/src', './mysrc')
        self.assertEqual(aliases.map('/ned/home/foo/src/a.py'), './mysrc/a.py')
        aliases = PathAliases()
        aliases.add('/ned/home/*/src/', './mysrc')
        self.assertEqual(aliases.map('/ned/home/foo/src/a.py'), './mysrc/a.py')

    def test_no_accidental_match(self):
        aliases = PathAliases()
        aliases.add('/home/*/src', './mysrc')
        self.assertEqual(aliases.map('/home/foo/srcetc'), '/home/foo/srcetc')

    def test_multiple_patterns(self):
        aliases = PathAliases()
        aliases.add('/home/*/src', './mysrc')
        aliases.add('/lib/*/libsrc', './mylib')
        self.assertEqual(aliases.map('/home/foo/src/a.py'), './mysrc/a.py')
        self.assertEqual(aliases.map('/lib/foo/libsrc/a.py'), './mylib/a.py')

    def test_cant_have_wildcard_at_end(self):
        aliases = PathAliases()
        self.assertRaisesRegexp(
            CoverageException, "Pattern must not end with wildcards.",
            aliases.add, "/ned/home/*", "fooey"
            )
        self.assertRaisesRegexp(
            CoverageException, "Pattern must not end with wildcards.",
            aliases.add, "/ned/home/*/", "fooey"
            )
        self.assertRaisesRegexp(
            CoverageException, "Pattern must not end with wildcards.",
            aliases.add, "/ned/home/*/*/", "fooey"
            )

    def test_no_accidental_munging(self):
        aliases = PathAliases()
        aliases.add(r'c:\Zoo\boo', 'src/')
        aliases.add('/home/ned$', 'src/')
        self.assertEqual(aliases.map(r'c:\Zoo\boo\foo.py'), 'src/foo.py')
        self.assertEqual(aliases.map(r'/home/ned$/foo.py'), 'src/foo.py')

    def test_paths_are_os_corrected(self):
        aliases = PathAliases()
        aliases.add('/home/ned/*/src', './mysrc')
        aliases.add(r'c:\ned\src', './mysrc')
        mapped = aliases.map(r'C:\Ned\src\sub\a.py')
        self.assertEqual(mapped, './mysrc/sub/a.py')

        aliases = PathAliases()
        aliases.add('/home/ned/*/src', r'.\mysrc')
        aliases.add(r'c:\ned\src', r'.\mysrc')
        mapped = aliases.map(r'/home/ned/foo/src/sub/a.py')
        self.assertEqual(mapped, r'.\mysrc\sub\a.py')

    def test_leading_wildcard(self):
        aliases = PathAliases()
        aliases.add('*/d1', './mysrc1')
        aliases.add('*/d2', './mysrc2')
        self.assertEqual(aliases.map('/foo/bar/d1/x.py'), './mysrc1/x.py')
        self.assertEqual(aliases.map('/foo/bar/d2/y.py'), './mysrc2/y.py')


class RelativePathAliasesTest(CoverageTest):
    """Tests for coverage/files.py:PathAliases, with relative files."""

    def test_dot(self):
        for d in ('.', '..', '../other', '~'):
            aliases = PathAliases()
            aliases.add(d, '/the/source')
            the_file = os.path.join(d, 'a.py')
            the_file = os.path.expanduser(the_file)
            the_file = os.path.abspath(the_file)

            assert '~' not in the_file  # to be sure the test is pure.
            self.assertEqual(aliases.map(the_file), '/the/source/a.py')


class FindPythonFilesTest(CoverageTest):
    """Tests of `find_python_files`."""

    def test_find_python_files(self):
        self.make_file("sub/a.py")
        self.make_file("sub/b.py")
        self.make_file("sub/x.c")                   # nope: not .py
        self.make_file("sub/ssub/__init__.py")
        self.make_file("sub/ssub/s.py")
        self.make_file("sub/ssub/~s.py")            # nope: editor effluvia
        self.make_file("sub/lab/exp.py")            # nope: no __init__.py
        self.make_file("sub/windows.pyw")
        py_files = set(find_python_files("sub"))
        self.assert_same_files(py_files, [
            "sub/a.py", "sub/b.py",
            "sub/ssub/__init__.py", "sub/ssub/s.py",
            "sub/windows.pyw",
            ])
