# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Test json-based summary reporting for coverage.py"""

from __future__ import annotations

import json
import os

from datetime import datetime
from typing import Any

import coverage
from coverage import Coverage
from coverage.jsonreport import FORMAT_VERSION

from tests.coveragetest import UsingModulesMixin, CoverageTest


class JsonReportTest(UsingModulesMixin, CoverageTest):
    """Tests of the JSON reports from coverage.py."""

    def _assert_expected_json_report(
        self,
        cov: Coverage,
        expected_result: dict[str, Any],
    ) -> None:
        """
        Helper that creates an example file for most tests.
        """
        self.make_file("a.py", """\
            a = {'b': 1}
            if a.get('a'):
                b = 1
            elif a.get('b'):
                b = 2
            else:
                b = 3
            if not a:
                b = 4
            """)
        self._compare_json_reports(cov, expected_result, "a")

    def _assert_expected_json_report_with_regions(
        self,
        cov: Coverage,
        expected_result: dict[str, Any],
    ) -> None:
        """
        Helper that creates an example file for regions tests.
        """
        self.make_file("b.py", """\
            a = {'b': 1}

            def c():
                return 1

            class C:
                pass

            class D:
                def e(self):
                    return 2
                def f(self):
                    return 3
            """)
        self._compare_json_reports(cov, expected_result, "b")

    def _compare_json_reports(
        self,
        cov: Coverage,
        expected_result: dict[str, Any],
        mod_name: str,
    ) -> None:
        """
        Helper that handles common ceremonies, comparing JSON reports that
        it creates to expected results, so tests can clearly show the
        consequences of setting various arguments.
        """
        mod = self.start_import_stop(cov, mod_name)
        output_path = os.path.join(self.temp_dir, f"{mod_name}.json")
        cov.json_report(mod, outfile=output_path)
        with open(output_path) as result_file:
            parsed_result = json.load(result_file)
        self.assert_recent_datetime(
            datetime.strptime(parsed_result['meta']['timestamp'], "%Y-%m-%dT%H:%M:%S.%f"),
        )
        del (parsed_result['meta']['timestamp'])
        expected_result["meta"].update({
            "format": FORMAT_VERSION,
            "version": coverage.__version__,
        })
        assert parsed_result == expected_result

    def test_branch_coverage(self) -> None:
        cov = coverage.Coverage(branch=True)
        expected_result = {
            'meta': {
                "branch_coverage": True,
                "show_contexts": False,
            },
            'files': {
                'a.py': {
                    'executed_lines': [1, 2, 4, 5, 8],
                    'missing_lines': [3, 7, 9],
                    'excluded_lines': [],
                    'executed_branches': [
                        [2, 4],
                        [4, 5],
                        [8, -1],
                    ],
                    'missing_branches': [
                        [2, 3],
                        [4, 7],
                        [8, 9],
                    ],
                    'summary': {
                        'missing_lines': 3,
                        'covered_lines': 5,
                        'num_statements': 8,
                        'num_branches': 6,
                        'excluded_lines': 0,
                        'num_partial_branches': 3,
                        'covered_branches': 3,
                        'missing_branches': 3,
                        'percent_covered': 57.142857142857146,
                        'percent_covered_display': '57',
                    },
                },
            },
            'totals': {
                'missing_lines': 3,
                'covered_lines': 5,
                'num_statements': 8,
                'num_branches': 6,
                'excluded_lines': 0,
                'num_partial_branches': 3,
                'percent_covered': 57.142857142857146,
                'percent_covered_display': '57',
                'covered_branches': 3,
                'missing_branches': 3,
            },
        }
        self._assert_expected_json_report(cov, expected_result)

    def test_simple_line_coverage(self) -> None:
        cov = coverage.Coverage()
        expected_result = {
            'meta': {
                "branch_coverage": False,
                "show_contexts": False,
            },
            'files': {
                'a.py': {
                    'executed_lines': [1, 2, 4, 5, 8],
                    'missing_lines': [3, 7, 9],
                    'excluded_lines': [],
                    'summary': {
                        'excluded_lines': 0,
                        'missing_lines': 3,
                        'covered_lines': 5,
                        'num_statements': 8,
                        'percent_covered': 62.5,
                        'percent_covered_display': '62',
                    },
                },
            },
            'totals': {
                'excluded_lines': 0,
                'missing_lines': 3,
                'covered_lines': 5,
                'num_statements': 8,
                'percent_covered': 62.5,
                'percent_covered_display': '62',
            },
        }
        self._assert_expected_json_report(cov, expected_result)

    def test_regions_coverage(self) -> None:
        cov = coverage.Coverage()
        expected_result = {
            "meta": {
                "branch_coverage": False,
                "show_contexts": False
            },
            "files": {
                "b.py": {
                    "executed_lines": [1, 3, 6, 7, 9, 10, 12],
                    "summary": {
                        "covered_lines": 7,
                        "num_statements": 10,
                        "percent_covered": 70.0,
                        "percent_covered_display": "70",
                        "missing_lines": 3,
                        "excluded_lines": 0
                    },
                    "missing_lines": [4, 11, 13],
                    "excluded_lines": [],
                    "function": {
                        "c": {
                            "executed_lines": [],
                            "summary": {
                                "covered_lines": 0,
                                "num_statements": 1,
                                "percent_covered": 0.0,
                                "percent_covered_display": "0",
                                "missing_lines": 1,
                                "excluded_lines": 0
                            },
                            "missing_lines": [4],
                            "excluded_lines": []
                        },
                        "D.e": {
                            "executed_lines": [],
                            "summary": {
                                "covered_lines": 0,
                                "num_statements": 1,
                                "percent_covered": 0.0,
                                "percent_covered_display": "0",
                                "missing_lines": 1,
                                "excluded_lines": 0
                            },
                            "missing_lines": [11],
                            "excluded_lines": []
                        },
                        "D.f": {
                            "executed_lines": [],
                            "summary": {
                                "covered_lines": 0,
                                "num_statements": 1,
                                "percent_covered": 0.0,
                                "percent_covered_display": "0",
                                "missing_lines": 1,
                                "excluded_lines": 0
                            },
                            "missing_lines": [13],
                            "excluded_lines": []
                        }
                    },
                    "class": {
                        "C": {
                            "executed_lines": [],
                            "summary": {
                                "covered_lines": 0,
                                "num_statements": 0,
                                "percent_covered": 100.0,
                                "percent_covered_display": "100",
                                "missing_lines": 0,
                                "excluded_lines": 0
                            },
                            "missing_lines": [],
                            "excluded_lines": []
                        },
                        "D": {
                            "executed_lines": [],
                            "summary": {
                                "covered_lines": 0,
                                "num_statements": 2,
                                "percent_covered": 0.0,
                                "percent_covered_display": "0",
                                "missing_lines": 2,
                                "excluded_lines": 0
                            },
                            "missing_lines": [11, 13],
                            "excluded_lines": []
                        }
                    }
                }
            },
            "totals": {
                "covered_lines": 7,
                "num_statements": 10,
                "percent_covered": 70.0,
                "percent_covered_display": "70",
                "missing_lines": 3,
                "excluded_lines": 0
            }
        }
        self._assert_expected_json_report_with_regions(cov, expected_result)

    def run_context_test(self, relative_files: bool) -> None:
        """A helper for two tests below."""
        self.make_file("config", f"""\
            [run]
            relative_files = {relative_files}

            [report]
            precision = 2

            [json]
            show_contexts = True
            """)
        cov = coverage.Coverage(context="cool_test", config_file="config")
        expected_result = {
            'meta': {
                "branch_coverage": False,
                "show_contexts": True,
            },
            'files': {
                'a.py': {
                    'executed_lines': [1, 2, 4, 5, 8],
                    'missing_lines': [3, 7, 9],
                    'excluded_lines': [],
                    "contexts": {
                        "1": [
                            "cool_test",
                        ],
                        "2": [
                            "cool_test",
                        ],
                        "4": [
                            "cool_test",
                        ],
                        "5": [
                            "cool_test",
                        ],
                        "8": [
                            "cool_test",
                        ],
                    },
                    'summary': {
                        'excluded_lines': 0,
                        'missing_lines': 3,
                        'covered_lines': 5,
                        'num_statements': 8,
                        'percent_covered': 62.5,
                        'percent_covered_display': '62.50',
                    },
                },
            },
            'totals': {
                'excluded_lines': 0,
                'missing_lines': 3,
                'covered_lines': 5,
                'num_statements': 8,
                'percent_covered': 62.5,
                'percent_covered_display': '62.50',
            },
        }
        self._assert_expected_json_report(cov, expected_result)

    def test_context_non_relative(self) -> None:
        self.run_context_test(relative_files=False)

    def test_context_relative(self) -> None:
        self.run_context_test(relative_files=True)
