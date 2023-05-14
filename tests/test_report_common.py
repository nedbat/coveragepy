# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Tests of behavior common to all reporting."""

from __future__ import annotations

import textwrap

import coverage
from coverage.files import abs_file

from tests.coveragetest import CoverageTest
from tests.goldtest import contains, doesnt_contain
from tests.helpers import arcz_to_arcs, os_sep


class ReportMapsPathsTest(CoverageTest):
    """Check that reporting implicitly maps paths."""

    def make_files(self, data: str, settings: bool = False) -> None:
        """Create the test files we need for line coverage."""
        src = """\
            if VER == 1:
                print("line 2")
            if VER == 2:
                print("line 4")
            if VER == 3:
                print("line 6")
            """
        self.make_file("src/program.py", src)
        self.make_file("ver1/program.py", src)
        self.make_file("ver2/program.py", src)

        if data == "line":
            self.make_data_file(
                lines={
                    abs_file("ver1/program.py"): [1, 2, 3, 5],
                    abs_file("ver2/program.py"): [1, 3, 4, 5],
                }
            )
        else:
            self.make_data_file(
                arcs={
                    abs_file("ver1/program.py"): arcz_to_arcs(".1 12 23 35 5."),
                    abs_file("ver2/program.py"): arcz_to_arcs(".1 13 34 45 5."),
                }
            )

        if settings:
            self.make_file(".coveragerc", """\
                [paths]
                source =
                    src
                    ver1
                    ver2
                """)

    def test_map_paths_during_line_report_without_setting(self) -> None:
        self.make_files(data="line")
        cov = coverage.Coverage()
        cov.load()
        cov.report(show_missing=True)
        expected = textwrap.dedent(os_sep("""\
            Name              Stmts   Miss  Cover   Missing
            -----------------------------------------------
            ver1/program.py       6      2    67%   4, 6
            ver2/program.py       6      2    67%   2, 6
            -----------------------------------------------
            TOTAL                12      4    67%
            """))
        assert expected == self.stdout()

    def test_map_paths_during_line_report(self) -> None:
        self.make_files(data="line", settings=True)
        cov = coverage.Coverage()
        cov.load()
        cov.report(show_missing=True)
        expected = textwrap.dedent(os_sep("""\
            Name             Stmts   Miss  Cover   Missing
            ----------------------------------------------
            src/program.py       6      1    83%   6
            ----------------------------------------------
            TOTAL                6      1    83%
            """))
        assert expected == self.stdout()

    def test_map_paths_during_branch_report_without_setting(self) -> None:
        self.make_files(data="arcs")
        cov = coverage.Coverage(branch=True)
        cov.load()
        cov.report(show_missing=True)
        expected = textwrap.dedent(os_sep("""\
            Name              Stmts   Miss Branch BrPart  Cover   Missing
            -------------------------------------------------------------
            ver1/program.py       6      2      6      3    58%   1->3, 4, 6
            ver2/program.py       6      2      6      3    58%   2, 3->5, 6
            -------------------------------------------------------------
            TOTAL                12      4     12      6    58%
            """))
        assert expected == self.stdout()

    def test_map_paths_during_branch_report(self) -> None:
        self.make_files(data="arcs", settings=True)
        cov = coverage.Coverage(branch=True)
        cov.load()
        cov.report(show_missing=True)
        expected = textwrap.dedent(os_sep("""\
            Name             Stmts   Miss Branch BrPart  Cover   Missing
            ------------------------------------------------------------
            src/program.py       6      1      6      1    83%   6
            ------------------------------------------------------------
            TOTAL                6      1      6      1    83%
            """))
        assert expected == self.stdout()

    def test_map_paths_during_annotate(self) -> None:
        self.make_files(data="line", settings=True)
        cov = coverage.Coverage()
        cov.load()
        cov.annotate()
        self.assert_exists(os_sep("src/program.py,cover"))
        self.assert_doesnt_exist(os_sep("ver1/program.py,cover"))
        self.assert_doesnt_exist(os_sep("ver2/program.py,cover"))

    def test_map_paths_during_html_report(self) -> None:
        self.make_files(data="line", settings=True)
        cov = coverage.Coverage()
        cov.load()
        cov.html_report()
        contains("htmlcov/index.html", os_sep("src/program.py"))
        doesnt_contain("htmlcov/index.html", os_sep("ver1/program.py"), os_sep("ver2/program.py"))

    def test_map_paths_during_xml_report(self) -> None:
        self.make_files(data="line", settings=True)
        cov = coverage.Coverage()
        cov.load()
        cov.xml_report()
        contains("coverage.xml", "src/program.py")
        doesnt_contain("coverage.xml", "ver1/program.py", "ver2/program.py")

    def test_map_paths_during_json_report(self) -> None:
        self.make_files(data="line", settings=True)
        cov = coverage.Coverage()
        cov.load()
        cov.json_report()
        def os_sepj(s: str) -> str:
            return os_sep(s).replace("\\", r"\\")
        contains("coverage.json", os_sepj("src/program.py"))
        doesnt_contain("coverage.json", os_sepj("ver1/program.py"), os_sepj("ver2/program.py"))

    def test_map_paths_during_lcov_report(self) -> None:
        self.make_files(data="line", settings=True)
        cov = coverage.Coverage()
        cov.load()
        cov.lcov_report()
        contains("coverage.lcov", os_sep("src/program.py"))
        doesnt_contain("coverage.lcov", os_sep("ver1/program.py"), os_sep("ver2/program.py"))
