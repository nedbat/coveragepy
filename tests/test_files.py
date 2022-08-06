# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Tests for files.py"""

import os
import os.path
from unittest import mock

import pytest

from coverage import env, files
from coverage.exceptions import ConfigError
from coverage.files import (
    FnmatchMatcher, ModuleMatcher, PathAliases, TreeMatcher, abs_file,
    actual_path, find_python_files, flat_rootname, fnmatches_to_regex,
)
from tests.coveragetest import CoverageTest


class FilesTest(CoverageTest):
    """Tests of coverage.files."""

    def abs_path(self, p):
        """Return the absolute path for `p`."""
        return os.path.join(abs_file(os.getcwd()), os.path.normpath(p))

    def test_simple(self):
        self.make_file("hello.py")
        files.set_relative_directory()
        assert files.relative_filename("hello.py") == "hello.py"
        a = self.abs_path("hello.py")
        assert a != "hello.py"
        assert files.relative_filename(a) == "hello.py"

    def test_peer_directories(self):
        self.make_file("sub/proj1/file1.py")
        self.make_file("sub/proj2/file2.py")
        a1 = self.abs_path("sub/proj1/file1.py")
        a2 = self.abs_path("sub/proj2/file2.py")
        d = os.path.normpath("sub/proj1")
        os.chdir(d)
        files.set_relative_directory()
        assert files.relative_filename(a1) == "file1.py"
        assert files.relative_filename(a2) == a2

    def test_filepath_contains_absolute_prefix_twice(self):
        # https://github.com/nedbat/coveragepy/issues/194
        # Build a path that has two pieces matching the absolute path prefix.
        # Technically, this test doesn't do that on Windows, but drive
        # letters make that impractical to achieve.
        files.set_relative_directory()
        d = abs_file(os.curdir)
        trick = os.path.splitdrive(d)[1].lstrip(os.path.sep)
        rel = os.path.join('sub', trick, 'file1.py')
        assert files.relative_filename(abs_file(rel)) == rel

    def test_canonical_filename_ensure_cache_hit(self):
        self.make_file("sub/proj1/file1.py")
        d = actual_path(self.abs_path("sub/proj1"))
        os.chdir(d)
        files.set_relative_directory()
        canonical_path = files.canonical_filename('sub/proj1/file1.py')
        assert canonical_path == self.abs_path('file1.py')
        # After the filename has been converted, it should be in the cache.
        assert 'sub/proj1/file1.py' in files.CANONICAL_FILENAME_CACHE
        assert files.canonical_filename('sub/proj1/file1.py') == self.abs_path('file1.py')

    @pytest.mark.parametrize(
        ["curdir", "sep"], [
            ("/", "/"),
            ("X:\\", "\\"),
        ]
    )
    def test_relative_dir_for_root(self, curdir, sep):
        with mock.patch.object(files.os, 'curdir', new=curdir):
            with mock.patch.object(files.os, 'sep', new=sep):
                with mock.patch('coverage.files.os.path.normcase', return_value=curdir):
                    files.set_relative_directory()
                    assert files.relative_directory() == curdir


@pytest.mark.parametrize("original, flat", [
    ("abc.py", "abc_py"),
    ("hellothere", "hellothere"),
    ("a/b/c.py", "d_86bbcbe134d28fd2_c_py"),
    ("a/b/defghi.py", "d_86bbcbe134d28fd2_defghi_py"),
    ("/a/b/c.py", "d_bb25e0ada04227c6_c_py"),
    ("/a/b/defghi.py", "d_bb25e0ada04227c6_defghi_py"),
    (r"c:\foo\bar.html", "d_e7c107482373f299_bar_html"),
    (r"d:\foo\bar.html", "d_584a05dcebc67b46_bar_html"),
    ("Montréal/☺/conf.py", "d_c840497a2c647ce0_conf_py"),
    ( # original:
        r"c:\lorem\ipsum\quia\dolor\sit\amet\consectetur\adipisci\velit\sed" +
        r"\quia\non\numquam\eius\modi\tempora\incidunt\ut\labore\et\dolore" +
        r"\magnam\aliquam\quaerat\voluptatem\ut\enim\ad\minima\veniam\quis" +
        r"\nostrum\exercitationem\ullam\corporis\suscipit\laboriosam" +
        r"\Montréal\☺\my_program.py",
        # flat:
        "d_e597dfacb73a23d5_my_program_py"
     ),
])
def test_flat_rootname(original, flat):
    assert flat_rootname(original) == flat


@pytest.mark.parametrize(
        "patterns, case_insensitive, partial," +
            "matches," +
            "nomatches",
[
    (
        ["abc", "xyz"], False, False,
            ["abc", "xyz"],
            ["ABC", "xYz", "abcx", "xabc", "axyz", "xyza"],
    ),
    (
        ["abc", "xyz"], True, False,
            ["abc", "xyz", "Abc", "XYZ", "AbC"],
            ["abcx", "xabc", "axyz", "xyza"],
    ),
    (
        ["abc/hi.py"], True, False,
            ["abc/hi.py", "ABC/hi.py", r"ABC\hi.py"],
            ["abc_hi.py", "abc/hi.pyc"],
    ),
    (
        [r"abc\hi.py"], True, False,
            [r"abc\hi.py", r"ABC\hi.py"],
            ["abc/hi.py", "ABC/hi.py", "abc_hi.py", "abc/hi.pyc"],
    ),
    (
        ["abc/*/hi.py"], True, False,
            ["abc/foo/hi.py", "ABC/foo/bar/hi.py", r"ABC\foo/bar/hi.py"],
            ["abc/hi.py", "abc/hi.pyc"],
    ),
    (
        ["abc/[a-f]*/hi.py"], True, False,
            ["abc/foo/hi.py", "ABC/foo/bar/hi.py", r"ABC\foo/bar/hi.py"],
            ["abc/zoo/hi.py", "abc/hi.py", "abc/hi.pyc"],
    ),
    (
        ["abc/"], True, True,
            ["abc/foo/hi.py", "ABC/foo/bar/hi.py", r"ABC\foo/bar/hi.py"],
            ["abcd/foo.py", "xabc/hi.py"],
    ),
])
def test_fnmatches_to_regex(patterns, case_insensitive, partial, matches, nomatches):
    regex = fnmatches_to_regex(patterns, case_insensitive=case_insensitive, partial=partial)
    for s in matches:
        assert regex.match(s)
    for s in nomatches:
        assert not regex.match(s)


class MatcherTest(CoverageTest):
    """Tests of file matchers."""

    def setUp(self):
        super().setUp()
        files.set_relative_directory()

    def assertMatches(self, matcher, filepath, matches):
        """The `matcher` should agree with `matches` about `filepath`."""
        canonical = files.canonical_filename(filepath)
        msg = f"File {filepath} should have matched as {matches}"
        assert matches == matcher.match(canonical), msg

    def test_tree_matcher(self):
        case_folding = env.WINDOWS
        matches_to_try = [
            (self.make_file("sub/file1.py"), True),
            (self.make_file("sub/file2.c"), True),
            (self.make_file("sub2/file3.h"), False),
            (self.make_file("sub3/file4.py"), True),
            (self.make_file("sub3/file5.c"), False),
            (self.make_file("sub4/File5.py"), case_folding),
            (self.make_file("sub5/file6.py"), case_folding),
        ]
        trees = [
            files.canonical_filename("sub"),
            files.canonical_filename("sub3/file4.py"),
            files.canonical_filename("sub4/file5.py"),
            files.canonical_filename("SUB5/file6.py"),
        ]
        tm = TreeMatcher(trees)
        assert tm.info() == sorted(trees)
        for filepath, matches in matches_to_try:
            self.assertMatches(tm, filepath, matches)

    def test_module_matcher(self):
        matches_to_try = [
            ('test', True),
            ('trash', False),
            ('testing', False),
            ('test.x', True),
            ('test.x.y.z', True),
            ('py', False),
            ('py.t', False),
            ('py.test', True),
            ('py.testing', False),
            ('py.test.buz', True),
            ('py.test.buz.baz', True),
            ('__main__', False),
            ('mymain', True),
            ('yourmain', False),
        ]
        modules = ['test', 'py.test', 'mymain']
        mm = ModuleMatcher(modules)
        assert mm.info() == modules
        for modulename, matches in matches_to_try:
            assert mm.match(modulename) == matches, modulename

    def test_fnmatch_matcher(self):
        matches_to_try = [
            (self.make_file("sub/file1.py"), True),
            (self.make_file("sub/file2.c"), False),
            (self.make_file("sub2/file3.h"), True),
            (self.make_file("sub3/file4.py"), True),
            (self.make_file("sub3/file5.c"), False),
        ]
        fnm = FnmatchMatcher(["*.py", "*/sub2/*"])
        assert fnm.info() == ["*.py", "*/sub2/*"]
        for filepath, matches in matches_to_try:
            self.assertMatches(fnm, filepath, matches)

    def test_fnmatch_matcher_overload(self):
        fnm = FnmatchMatcher(["*x%03d*.txt" % i for i in range(500)])
        self.assertMatches(fnm, "x007foo.txt", True)
        self.assertMatches(fnm, "x123foo.txt", True)
        self.assertMatches(fnm, "x798bar.txt", False)

    def test_fnmatch_windows_paths(self):
        # We should be able to match Windows paths even if we are running on
        # a non-Windows OS.
        fnm = FnmatchMatcher(["*/foo.py"])
        self.assertMatches(fnm, r"dir\foo.py", True)
        fnm = FnmatchMatcher([r"*\foo.py"])
        self.assertMatches(fnm, r"dir\foo.py", True)


@pytest.fixture(params=[False, True], name="rel_yn")
def relative_setting(request):
    """Parameterized fixture to choose whether PathAliases is relative or not."""
    return request.param


class PathAliasesTest(CoverageTest):
    """Tests for coverage/files.py:PathAliases"""

    run_in_temp_dir = False

    def assert_mapped(self, aliases, inp, out, relative=False):
        """Assert that `inp` mapped through `aliases` produces `out`.

        `out` is canonicalized first, since aliases produce canonicalized
        paths by default.

        """
        mapped = aliases.map(inp)
        expected = files.canonical_filename(out) if not relative else out
        assert mapped == expected

    def assert_unchanged(self, aliases, inp):
        """Assert that `inp` mapped through `aliases` is unchanged."""
        assert aliases.map(inp) == inp

    def test_noop(self, rel_yn):
        aliases = PathAliases(relative=rel_yn)
        self.assert_unchanged(aliases, '/ned/home/a.py')

    def test_nomatch(self, rel_yn):
        aliases = PathAliases(relative=rel_yn)
        aliases.add('/home/*/src', './mysrc')
        self.assert_unchanged(aliases, '/home/foo/a.py')

    def test_wildcard(self, rel_yn):
        aliases = PathAliases(relative=rel_yn)
        aliases.add('/ned/home/*/src', './mysrc')
        self.assert_mapped(aliases, '/ned/home/foo/src/a.py', './mysrc/a.py', relative=rel_yn)

        aliases = PathAliases(relative=rel_yn)
        aliases.add('/ned/home/*/src/', './mysrc')
        self.assert_mapped(aliases, '/ned/home/foo/src/a.py', './mysrc/a.py', relative=rel_yn)

    def test_no_accidental_match(self, rel_yn):
        aliases = PathAliases(relative=rel_yn)
        aliases.add('/home/*/src', './mysrc')
        self.assert_unchanged(aliases, '/home/foo/srcetc')

    def test_multiple_patterns(self, rel_yn):
        aliases = PathAliases(relative=rel_yn)
        aliases.add('/home/*/src', './mysrc')
        aliases.add('/lib/*/libsrc', './mylib')
        self.assert_mapped(aliases, '/home/foo/src/a.py', './mysrc/a.py', relative=rel_yn)
        self.assert_mapped(aliases, '/lib/foo/libsrc/a.py', './mylib/a.py', relative=rel_yn)

    @pytest.mark.parametrize("badpat", [
        "/ned/home/*",
        "/ned/home/*/",
        "/ned/home/*/*/",
    ])
    def test_cant_have_wildcard_at_end(self, badpat):
        aliases = PathAliases()
        msg = "Pattern must not end with wildcards."
        with pytest.raises(ConfigError, match=msg):
            aliases.add(badpat, "fooey")

    def test_no_accidental_munging(self):
        aliases = PathAliases()
        aliases.add(r'c:\Zoo\boo', 'src/')
        aliases.add('/home/ned$', 'src/')
        self.assert_mapped(aliases, r'c:\Zoo\boo\foo.py', 'src/foo.py')
        self.assert_mapped(aliases, r'/home/ned$/foo.py', 'src/foo.py')

    def test_paths_are_os_corrected(self, rel_yn):
        aliases = PathAliases(relative=rel_yn)
        aliases.add('/home/ned/*/src', './mysrc')
        aliases.add(r'c:\ned\src', './mysrc')
        self.assert_mapped(aliases, r'C:\Ned\src\sub\a.py', './mysrc/sub/a.py', relative=rel_yn)

        aliases = PathAliases(relative=rel_yn)
        aliases.add('/home/ned/*/src', r'.\mysrc')
        aliases.add(r'c:\ned\src', r'.\mysrc')
        self.assert_mapped(
            aliases,
            r'/home/ned/foo/src/sub/a.py',
            r'.\mysrc\sub\a.py',
            relative=rel_yn,
        )

    def test_windows_on_linux(self, rel_yn):
        # https://github.com/nedbat/coveragepy/issues/618
        lin = "*/project/module/"
        win = "*\\project\\module\\"

        # Try the paths in both orders.
        for paths in [[lin, win], [win, lin]]:
            aliases = PathAliases(relative=rel_yn)
            for path in paths:
                aliases.add(path, "project/module")
            self.assert_mapped(
                aliases,
                "C:\\a\\path\\somewhere\\coveragepy_test\\project\\module\\tests\\file.py",
                "project/module/tests/file.py",
                relative=rel_yn,
            )

    def test_linux_on_windows(self, rel_yn):
        # https://github.com/nedbat/coveragepy/issues/618
        lin = "*/project/module/"
        win = "*\\project\\module\\"

        # Try the paths in both orders.
        for paths in [[lin, win], [win, lin]]:
            aliases = PathAliases(relative=rel_yn)
            for path in paths:
                aliases.add(path, "project\\module")
            self.assert_mapped(
                aliases,
                "C:/a/path/somewhere/coveragepy_test/project/module/tests/file.py",
                "project\\module\\tests\\file.py",
                relative=rel_yn,
            )

    def test_multiple_wildcard(self, rel_yn):
        aliases = PathAliases(relative=rel_yn)
        aliases.add('/home/jenkins/*/a/*/b/*/django', './django')
        self.assert_mapped(
            aliases,
            '/home/jenkins/xx/a/yy/b/zz/django/foo/bar.py',
            './django/foo/bar.py',
            relative=rel_yn,
        )

    def test_windows_root_paths(self, rel_yn):
        aliases = PathAliases(relative=rel_yn)
        aliases.add('X:\\', '/tmp/src')
        self.assert_mapped(
            aliases,
            "X:\\a\\file.py",
            "/tmp/src/a/file.py",
            relative=rel_yn,
        )
        self.assert_mapped(
            aliases,
            "X:\\file.py",
            "/tmp/src/file.py",
            relative=rel_yn,
        )

    def test_leading_wildcard(self, rel_yn):
        aliases = PathAliases(relative=rel_yn)
        aliases.add('*/d1', './mysrc1')
        aliases.add('*/d2', './mysrc2')
        self.assert_mapped(aliases, '/foo/bar/d1/x.py', './mysrc1/x.py', relative=rel_yn)
        self.assert_mapped(aliases, '/foo/bar/d2/y.py', './mysrc2/y.py', relative=rel_yn)

    # The root test case was added for the manylinux Docker images,
    # and I'm not sure how it should work on Windows, so skip it.
    cases = [".", "..", "../other"]
    if not env.WINDOWS:
        cases += ["/"]
    @pytest.mark.parametrize("dirname", cases)
    def test_dot(self, dirname):
        aliases = PathAliases()
        aliases.add(dirname, '/the/source')
        the_file = os.path.join(dirname, 'a.py')
        the_file = os.path.expanduser(the_file)
        the_file = os.path.abspath(os.path.realpath(the_file))

        assert '~' not in the_file  # to be sure the test is pure.
        self.assert_mapped(aliases, the_file, '/the/source/a.py')


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


@pytest.mark.skipif(not env.WINDOWS, reason="Only need to run Windows tests on Windows.")
class WindowsFileTest(CoverageTest):
    """Windows-specific tests of file name handling."""

    run_in_temp_dir = False

    def test_actual_path(self):
        assert actual_path(r'c:\Windows') == actual_path(r'C:\wINDOWS')
