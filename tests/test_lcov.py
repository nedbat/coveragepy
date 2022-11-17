# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Test LCOV-based summary reporting for coverage.py."""

import textwrap

from tests.coveragetest import CoverageTest

import coverage
from coverage import env


class LcovTest(CoverageTest):
    """Tests of the LCOV reports from coverage.py."""

    def create_initial_files(self):
        """
        Helper for tests that handles the common ceremony so the tests can
        show the consequences of changes in the setup.
        """
        self.make_file("main_file.py", """\
            #!/usr/bin/env python3

            def cuboid_volume(l):
                return (l*l*l)

            def IsItTrue():
                return True
            """)

        self.make_file("test_file.py", """\
            #!/usr/bin/env python3

            from main_file import cuboid_volume
            import unittest

            class TestCuboid(unittest.TestCase):
                def test_volume(self):
                    self.assertAlmostEqual(cuboid_volume(2),8)
                    self.assertAlmostEqual(cuboid_volume(1),1)
                    self.assertAlmostEqual(cuboid_volume(0),0)
                    self.assertAlmostEqual(cuboid_volume(5.5),166.375)
            """)

    def get_lcov_report_content(self, filename="coverage.lcov"):
        """Return the content of an LCOV report."""
        with open(filename, "r") as file:
            file_contents = file.read()
        return file_contents

    def test_lone_file(self):
        """For a single file with a couple of functions, the lcov should cover
        the function definitions themselves, but not the returns."""
        self.make_file("main_file.py", """\
            #!/usr/bin/env python3

            def cuboid_volume(l):
                return (l*l*l)

            def IsItTrue():
                return True
            """)
        expected_result = textwrap.dedent("""\
            TN:
            SF:main_file.py
            DA:3,1,7URou3io0zReBkk69lEb/Q
            DA:6,1,ilhb4KUfytxtEuClijZPlQ
            DA:4,0,Xqj6H1iz/nsARMCAbE90ng
            DA:7,0,LWILTcvARcydjFFyo9qM0A
            LF:4
            LH:2
            end_of_record
            """)
        self.assert_doesnt_exist(".coverage")
        cov = coverage.Coverage(source=["."])
        self.start_import_stop(cov, "main_file")
        cov.lcov_report()
        actual_result = self.get_lcov_report_content()
        assert expected_result == actual_result

    def test_simple_line_coverage_two_files(self):
        """Test that line coverage is created when coverage is run,
        and matches the output of the file below."""
        self.create_initial_files()
        self.assert_doesnt_exist(".coverage")
        self.make_file(".coveragerc", "[lcov]\noutput = data.lcov\n")
        cov = coverage.Coverage(source=".")
        self.start_import_stop(cov, "test_file")
        cov.lcov_report()
        self.assert_exists("data.lcov")
        expected_result = textwrap.dedent("""\
            TN:
            SF:main_file.py
            DA:3,1,7URou3io0zReBkk69lEb/Q
            DA:6,1,ilhb4KUfytxtEuClijZPlQ
            DA:4,0,Xqj6H1iz/nsARMCAbE90ng
            DA:7,0,LWILTcvARcydjFFyo9qM0A
            LF:4
            LH:2
            end_of_record
            TN:
            SF:test_file.py
            DA:3,1,R5Rb4IzmjKRgY/vFFc1TRg
            DA:4,1,E/tvV9JPVDhEcTCkgrwOFw
            DA:6,1,GP08LPBYJq8EzYveHJy2qA
            DA:7,1,MV+jSLi6PFEl+WatEAptog
            DA:8,0,qyqd1mF289dg6oQAQHA+gQ
            DA:9,0,nmEYd5F1KrxemgC9iVjlqg
            DA:10,0,jodMK26WYDizOO1C7ekBbg
            DA:11,0,LtxfKehkX8o4KvC5GnN52g
            LF:8
            LH:4
            end_of_record
            """)
        actual_result = self.get_lcov_report_content(filename="data.lcov")
        assert expected_result == actual_result

    def test_branch_coverage_one_file(self):
        """Test that the reporter produces valid branch coverage."""
        self.make_file("main_file.py", """\
            #!/usr/bin/env python3

            def is_it_x(x):
                if x == 3:
                    return x
                else:
                    return False
            """)
        self.assert_doesnt_exist(".coverage")
        cov = coverage.Coverage(branch=True, source=".")
        self.start_import_stop(cov, "main_file")
        cov.lcov_report()
        self.assert_exists("coverage.lcov")
        expected_result = textwrap.dedent("""\
            TN:
            SF:main_file.py
            DA:3,1,4MDXMbvwQ3L7va1tsphVzw
            DA:4,0,MuERA6EYyZNpKPqoJfzwkA
            DA:5,0,sAyiiE6iAuPMte9kyd0+3g
            DA:7,0,W/g8GJDAYJkSSurt59Mzfw
            LF:4
            LH:1
            BRDA:5,0,0,-
            BRDA:7,0,1,-
            BRF:2
            BRH:0
            end_of_record
            """)
        actual_result = self.get_lcov_report_content()
        assert expected_result == actual_result

    def test_branch_coverage_two_files(self):
        """Test that valid branch coverage is generated
        in the case of two files."""
        self.make_file("main_file.py", """\
            #!/usr/bin/env python3

            def is_it_x(x):
                if x == 3:
                    return x
                else:
                    return False
            """)

        self.make_file("test_file.py", """\
            #!/usr/bin/env python3

            from main_file import *
            import unittest

            class TestIsItX(unittest.TestCase):
                def test_is_it_x(self):
                    self.assertEqual(is_it_x(3), 3)
                    self.assertEqual(is_it_x(4), False)
            """)
        self.assert_doesnt_exist(".coverage")
        cov = coverage.Coverage(branch=True, source=".")
        self.start_import_stop(cov, "test_file")
        cov.lcov_report()
        self.assert_exists("coverage.lcov")
        expected_result = textwrap.dedent("""\
            TN:
            SF:main_file.py
            DA:3,1,4MDXMbvwQ3L7va1tsphVzw
            DA:4,0,MuERA6EYyZNpKPqoJfzwkA
            DA:5,0,sAyiiE6iAuPMte9kyd0+3g
            DA:7,0,W/g8GJDAYJkSSurt59Mzfw
            LF:4
            LH:1
            BRDA:5,0,0,-
            BRDA:7,0,1,-
            BRF:2
            BRH:0
            end_of_record
            TN:
            SF:test_file.py
            DA:3,1,9TxKIyoBtmhopmlbDNa8FQ
            DA:4,1,E/tvV9JPVDhEcTCkgrwOFw
            DA:6,1,C3s/c8C1Yd/zoNG1GnGexg
            DA:7,1,9qPyWexYysgeKtB+YvuzAg
            DA:8,0,LycuNcdqoUhPXeuXUTf5lA
            DA:9,0,FPTWzd68bDx76HN7VHu1wA
            LF:6
            LH:4
            BRF:0
            BRH:0
            end_of_record
            """)
        actual_result = self.get_lcov_report_content()
        assert actual_result == expected_result

    def test_half_covered_branch(self):
        """Test that for a given branch that is only half covered,
        the block numbers remain the same, and produces valid lcov.
        """
        self.make_file("main_file.py", """\
            something = True

            if something:
                print("Yes, something")
            else:
                print("No, nothing")
            """)
        self.assert_doesnt_exist(".coverage")
        cov = coverage.Coverage(branch=True, source=".")
        self.start_import_stop(cov, "main_file")
        cov.lcov_report()
        self.assert_exists("coverage.lcov")
        expected_result = textwrap.dedent("""\
            TN:
            SF:main_file.py
            DA:1,1,N4kbVOlkNI1rqOfCArBClw
            DA:3,1,CmlqqPf0/H+R/p7/PLEXZw
            DA:4,1,rE3mWnpoMq2W2sMETVk/uQ
            DA:6,0,+Aov7ekIts7C96udNDVIIQ
            LF:4
            LH:3
            BRDA:6,0,0,-
            BRDA:4,0,1,1
            BRF:2
            BRH:1
            end_of_record
            """)
        actual_result = self.get_lcov_report_content()
        assert actual_result == expected_result

    def test_empty_init_files(self):
        """Test that in the case of an empty __init__.py file, the lcov
        reporter will note that the file is there, and will note the empty
        line. It will also note the lack of branches, and the checksum for
        the line.

        Although there are no lines found, it will note one line as hit in
        old Pythons, and no lines hit in newer Pythons.
        """

        self.make_file("__init__.py", "")
        self.assert_doesnt_exist(".coverage")
        cov = coverage.Coverage(branch=True, source=".")
        self.start_import_stop(cov, "__init__")
        cov.lcov_report()
        self.assert_exists("coverage.lcov")
        # Newer Pythons have truly empty empty files.
        if env.PYBEHAVIOR.empty_is_empty:
            expected_result = textwrap.dedent("""\
                TN:
                SF:__init__.py
                LF:0
                LH:0
                BRF:0
                BRH:0
                end_of_record
                """)
        else:
            expected_result = textwrap.dedent("""\
                TN:
                SF:__init__.py
                DA:1,1,1B2M2Y8AsgTpgAmY7PhCfg
                LF:0
                LH:1
                BRF:0
                BRH:0
                end_of_record
                """)
        actual_result = self.get_lcov_report_content()
        assert actual_result == expected_result
