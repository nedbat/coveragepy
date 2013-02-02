"""Tests for coverage.codeunit"""

import os, sys

from coverage.codeunit import code_unit_factory
from coverage.files import FileLocator

from tests.coveragetest import CoverageTest

# pylint: disable=F0401
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
        acu = code_unit_factory("aa/afile.py", FileLocator())
        bcu = code_unit_factory("aa/bb/bfile.py", FileLocator())
        ccu = code_unit_factory("aa/bb/cc/cfile.py", FileLocator())
        self.assertEqual(acu[0].name, "aa/afile")
        self.assertEqual(bcu[0].name, "aa/bb/bfile")
        self.assertEqual(ccu[0].name, "aa/bb/cc/cfile")
        self.assertEqual(acu[0].flat_rootname(), "aa_afile")
        self.assertEqual(bcu[0].flat_rootname(), "aa_bb_bfile")
        self.assertEqual(ccu[0].flat_rootname(), "aa_bb_cc_cfile")
        self.assertEqual(acu[0].source_file().read(), "# afile.py\n")
        self.assertEqual(bcu[0].source_file().read(), "# bfile.py\n")
        self.assertEqual(ccu[0].source_file().read(), "# cfile.py\n")

    def test_odd_filenames(self):
        acu = code_unit_factory("aa/afile.odd.py", FileLocator())
        bcu = code_unit_factory("aa/bb/bfile.odd.py", FileLocator())
        b2cu = code_unit_factory("aa/bb.odd/bfile.py", FileLocator())
        self.assertEqual(acu[0].name, "aa/afile.odd")
        self.assertEqual(bcu[0].name, "aa/bb/bfile.odd")
        self.assertEqual(b2cu[0].name, "aa/bb.odd/bfile")
        self.assertEqual(acu[0].flat_rootname(), "aa_afile_odd")
        self.assertEqual(bcu[0].flat_rootname(), "aa_bb_bfile_odd")
        self.assertEqual(b2cu[0].flat_rootname(), "aa_bb_odd_bfile")
        self.assertEqual(acu[0].source_file().read(), "# afile.odd.py\n")
        self.assertEqual(bcu[0].source_file().read(), "# bfile.odd.py\n")
        self.assertEqual(b2cu[0].source_file().read(), "# bfile.py\n")

    def test_modules(self):
        import aa, aa.bb, aa.bb.cc
        cu = code_unit_factory([aa, aa.bb, aa.bb.cc], FileLocator())
        self.assertEqual(cu[0].name, "aa")
        self.assertEqual(cu[1].name, "aa.bb")
        self.assertEqual(cu[2].name, "aa.bb.cc")
        self.assertEqual(cu[0].flat_rootname(), "aa")
        self.assertEqual(cu[1].flat_rootname(), "aa_bb")
        self.assertEqual(cu[2].flat_rootname(), "aa_bb_cc")
        self.assertEqual(cu[0].source_file().read(), "# aa\n")
        self.assertEqual(cu[1].source_file().read(), "# bb\n")
        self.assertEqual(cu[2].source_file().read(), "")  # yes, empty

    def test_module_files(self):
        import aa.afile, aa.bb.bfile, aa.bb.cc.cfile
        cu = code_unit_factory([aa.afile, aa.bb.bfile, aa.bb.cc.cfile],
                                                                FileLocator())
        self.assertEqual(cu[0].name, "aa.afile")
        self.assertEqual(cu[1].name, "aa.bb.bfile")
        self.assertEqual(cu[2].name, "aa.bb.cc.cfile")
        self.assertEqual(cu[0].flat_rootname(), "aa_afile")
        self.assertEqual(cu[1].flat_rootname(), "aa_bb_bfile")
        self.assertEqual(cu[2].flat_rootname(), "aa_bb_cc_cfile")
        self.assertEqual(cu[0].source_file().read(), "# afile.py\n")
        self.assertEqual(cu[1].source_file().read(), "# bfile.py\n")
        self.assertEqual(cu[2].source_file().read(), "# cfile.py\n")

    def test_comparison(self):
        acu = code_unit_factory("aa/afile.py", FileLocator())[0]
        acu2 = code_unit_factory("aa/afile.py", FileLocator())[0]
        zcu = code_unit_factory("aa/zfile.py", FileLocator())[0]
        bcu = code_unit_factory("aa/bb/bfile.py", FileLocator())[0]
        assert acu == acu2 and acu <= acu2 and acu >= acu2
        assert acu < zcu and acu <= zcu and acu != zcu
        assert zcu > acu and zcu >= acu and zcu != acu
        assert acu < bcu and acu <= bcu and acu != bcu
        assert bcu > acu and bcu >= acu and bcu != acu

    def test_egg(self):
        # Test that we can get files out of eggs, and read their source files.
        # The egg1 module is installed by an action in igor.py.
        import egg1, egg1.egg1
        # Verify that we really imported from an egg.  If we did, then the
        # __file__ won't be an actual file, because one of the "directories"
        # in the path is actually the .egg zip file.
        self.assert_doesnt_exist(egg1.__file__)

        cu = code_unit_factory([egg1, egg1.egg1], FileLocator())
        self.assertEqual(cu[0].source_file().read(), "")
        self.assertEqual(cu[1].source_file().read().split("\n")[0],
                "# My egg file!"
                )
