"""Tests for FileReporters"""

import os
import sys

from coverage.plugin import FileReporter
from coverage.python import PythonFileReporter

from tests.coveragetest import CoverageTest

# pylint: disable=import-error
# Unable to import 'aa' (No module named aa)


def native(filename):
    """Make `filename` into a native form."""
    return filename.replace("/", os.sep)


class FileReporterTest(CoverageTest):
    """Tests for FileReporter classes."""

    run_in_temp_dir = False

    def setUp(self):
        super(FileReporterTest, self).setUp()
        # Parent class saves and restores sys.path, we can just modify it.
        testmods = self.nice_file(os.path.dirname(__file__), 'modules')
        sys.path.append(testmods)

    def test_filenames(self):
        acu = PythonFileReporter("aa/afile.py")
        bcu = PythonFileReporter("aa/bb/bfile.py")
        ccu = PythonFileReporter("aa/bb/cc/cfile.py")
        self.assertEqual(acu.relative_filename(), "aa/afile.py")
        self.assertEqual(bcu.relative_filename(), "aa/bb/bfile.py")
        self.assertEqual(ccu.relative_filename(), "aa/bb/cc/cfile.py")
        self.assertEqual(acu.flat_rootname(), "aa_afile_py")
        self.assertEqual(bcu.flat_rootname(), "aa_bb_bfile_py")
        self.assertEqual(ccu.flat_rootname(), "aa_bb_cc_cfile_py")
        self.assertEqual(acu.source(), "# afile.py\n")
        self.assertEqual(bcu.source(), "# bfile.py\n")
        self.assertEqual(ccu.source(), "# cfile.py\n")

    def test_odd_filenames(self):
        acu = PythonFileReporter("aa/afile.odd.py")
        bcu = PythonFileReporter("aa/bb/bfile.odd.py")
        b2cu = PythonFileReporter("aa/bb.odd/bfile.py")
        self.assertEqual(acu.relative_filename(), "aa/afile.odd.py")
        self.assertEqual(bcu.relative_filename(), "aa/bb/bfile.odd.py")
        self.assertEqual(b2cu.relative_filename(), "aa/bb.odd/bfile.py")
        self.assertEqual(acu.flat_rootname(), "aa_afile_odd_py")
        self.assertEqual(bcu.flat_rootname(), "aa_bb_bfile_odd_py")
        self.assertEqual(b2cu.flat_rootname(), "aa_bb_odd_bfile_py")
        self.assertEqual(acu.source(), "# afile.odd.py\n")
        self.assertEqual(bcu.source(), "# bfile.odd.py\n")
        self.assertEqual(b2cu.source(), "# bfile.py\n")

    def test_modules(self):
        import aa
        import aa.bb
        import aa.bb.cc

        acu = PythonFileReporter(aa)
        bcu = PythonFileReporter(aa.bb)
        ccu = PythonFileReporter(aa.bb.cc)
        self.assertEqual(acu.relative_filename(), native("aa.py"))
        self.assertEqual(bcu.relative_filename(), native("aa/bb.py"))
        self.assertEqual(ccu.relative_filename(), native("aa/bb/cc.py"))
        self.assertEqual(acu.flat_rootname(), "aa_py")
        self.assertEqual(bcu.flat_rootname(), "aa_bb_py")
        self.assertEqual(ccu.flat_rootname(), "aa_bb_cc_py")
        self.assertEqual(acu.source(), "# aa\n")
        self.assertEqual(bcu.source(), "# bb\n")
        self.assertEqual(ccu.source(), "")  # yes, empty

    def test_module_files(self):
        import aa.afile
        import aa.bb.bfile
        import aa.bb.cc.cfile

        acu = PythonFileReporter(aa.afile)
        bcu = PythonFileReporter(aa.bb.bfile)
        ccu = PythonFileReporter(aa.bb.cc.cfile)
        self.assertEqual(acu.relative_filename(), native("aa/afile.py"))
        self.assertEqual(bcu.relative_filename(), native("aa/bb/bfile.py"))
        self.assertEqual(ccu.relative_filename(), native("aa/bb/cc/cfile.py"))
        self.assertEqual(acu.flat_rootname(), "aa_afile_py")
        self.assertEqual(bcu.flat_rootname(), "aa_bb_bfile_py")
        self.assertEqual(ccu.flat_rootname(), "aa_bb_cc_cfile_py")
        self.assertEqual(acu.source(), "# afile.py\n")
        self.assertEqual(bcu.source(), "# bfile.py\n")
        self.assertEqual(ccu.source(), "# cfile.py\n")

    def test_comparison(self):
        acu = FileReporter("aa/afile.py")
        acu2 = FileReporter("aa/afile.py")
        zcu = FileReporter("aa/zfile.py")
        bcu = FileReporter("aa/bb/bfile.py")
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

        ecu = PythonFileReporter(egg1)
        eecu = PythonFileReporter(egg1.egg1)
        self.assertEqual(ecu.source(), u"")
        self.assertEqual(eecu.source().split("\n")[0], u"# My egg file!")
