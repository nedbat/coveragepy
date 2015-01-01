"""Tests for coverage.codeunit"""

import os
import sys

from coverage.codeunit import CodeUnit, PythonCodeUnit, code_units_factory

from tests.coveragetest import CoverageTest

# pylint: disable=import-error
# Unable to import 'aa' (No module named aa)


class CodeUnitTest(CoverageTest):
    """Tests for coverage.codeunit"""

    run_in_temp_dir = False

    def setUp(self):
        super(CodeUnitTest, self).setUp()
        # Parent class saves and restores sys.path, we can just modify it.
        testmods = self.nice_file(os.path.dirname(__file__), 'modules')
        sys.path.append(testmods)

    def test_filenames(self):
        acu = PythonCodeUnit("aa/afile.py")
        bcu = PythonCodeUnit("aa/bb/bfile.py")
        ccu = PythonCodeUnit("aa/bb/cc/cfile.py")
        self.assertEqual(acu.name, "aa/afile")
        self.assertEqual(bcu.name, "aa/bb/bfile")
        self.assertEqual(ccu.name, "aa/bb/cc/cfile")
        self.assertEqual(acu.flat_rootname(), "aa_afile")
        self.assertEqual(bcu.flat_rootname(), "aa_bb_bfile")
        self.assertEqual(ccu.flat_rootname(), "aa_bb_cc_cfile")
        self.assertEqual(acu.source(), "# afile.py\n")
        self.assertEqual(bcu.source(), "# bfile.py\n")
        self.assertEqual(ccu.source(), "# cfile.py\n")

    def test_odd_filenames(self):
        acu = PythonCodeUnit("aa/afile.odd.py")
        bcu = PythonCodeUnit("aa/bb/bfile.odd.py")
        b2cu = PythonCodeUnit("aa/bb.odd/bfile.py")
        self.assertEqual(acu.name, "aa/afile.odd")
        self.assertEqual(bcu.name, "aa/bb/bfile.odd")
        self.assertEqual(b2cu.name, "aa/bb.odd/bfile")
        self.assertEqual(acu.flat_rootname(), "aa_afile_odd")
        self.assertEqual(bcu.flat_rootname(), "aa_bb_bfile_odd")
        self.assertEqual(b2cu.flat_rootname(), "aa_bb_odd_bfile")
        self.assertEqual(acu.source(), "# afile.odd.py\n")
        self.assertEqual(bcu.source(), "# bfile.odd.py\n")
        self.assertEqual(b2cu.source(), "# bfile.py\n")

    def test_modules(self):
        import aa
        import aa.bb
        import aa.bb.cc

        cu = code_units_factory([aa, aa.bb, aa.bb.cc])
        self.assertEqual(cu[0].name, "aa")
        self.assertEqual(cu[1].name, "aa.bb")
        self.assertEqual(cu[2].name, "aa.bb.cc")
        self.assertEqual(cu[0].flat_rootname(), "aa")
        self.assertEqual(cu[1].flat_rootname(), "aa_bb")
        self.assertEqual(cu[2].flat_rootname(), "aa_bb_cc")
        self.assertEqual(cu[0].source(), "# aa\n")
        self.assertEqual(cu[1].source(), "# bb\n")
        self.assertEqual(cu[2].source(), "")  # yes, empty

    def test_module_files(self):
        import aa.afile
        import aa.bb.bfile
        import aa.bb.cc.cfile

        cu = code_units_factory([aa.afile, aa.bb.bfile, aa.bb.cc.cfile])
        self.assertEqual(cu[0].name, "aa.afile")
        self.assertEqual(cu[1].name, "aa.bb.bfile")
        self.assertEqual(cu[2].name, "aa.bb.cc.cfile")
        self.assertEqual(cu[0].flat_rootname(), "aa_afile")
        self.assertEqual(cu[1].flat_rootname(), "aa_bb_bfile")
        self.assertEqual(cu[2].flat_rootname(), "aa_bb_cc_cfile")
        self.assertEqual(cu[0].source(), "# afile.py\n")
        self.assertEqual(cu[1].source(), "# bfile.py\n")
        self.assertEqual(cu[2].source(), "# cfile.py\n")

    def test_comparison(self):
        acu = CodeUnit("aa/afile.py")
        acu2 = CodeUnit("aa/afile.py")
        zcu = CodeUnit("aa/zfile.py")
        bcu = CodeUnit("aa/bb/bfile.py")
        assert acu == acu2 and acu <= acu2 and acu >= acu2
        assert acu < zcu and acu <= zcu and acu != zcu
        assert zcu > acu and zcu >= acu and zcu != acu
        assert acu < bcu and acu <= bcu and acu != bcu
        assert bcu > acu and bcu >= acu and bcu != acu

    def test_egg(self):
        # Test that we can get files out of eggs, and read their source files.
        # The egg1 module is installed by an action in igor.py.
        import egg1
        import egg1.egg1

        # Verify that we really imported from an egg.  If we did, then the
        # __file__ won't be an actual file, because one of the "directories"
        # in the path is actually the .egg zip file.
        self.assert_doesnt_exist(egg1.__file__)

        cu = code_units_factory([egg1, egg1.egg1])
        self.assertEqual(cu[0].source(), u"")
        self.assertEqual(cu[1].source().split("\n")[0], u"# My egg file!")
