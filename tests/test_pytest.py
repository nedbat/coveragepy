"""Tests coverage measured within pytest modules."""

from __future__ import annotations

from tests.coveragetest import CoverageTest
import pytest
import json


class PytestTest(CoverageTest):
    """Tests coverage measured within pytest modules."""

    @pytest.mark.parametrize("with_pytest", [False, True])
    def test_branch_coverage(self, with_pytest) -> None:
        self.make_file("test_it.py", """\
            def test_it():
                c = 1
                if c:
                    print("I see c")

            if __name__ == "__main__":
                test_it()
            """)

        self.assert_doesnt_exist(".coverage")
        self.run_command(f"coverage run --branch {'-m pytest' if with_pytest else ''} test_it.py")
        self.assert_exists(".coverage")

        # XXX read with coverage.CoverageData().read() instead?
        self.run_command("coverage json")
        with open("coverage.json") as f:
            cov = json.load(f)

#        print(json.dumps(cov, indent=4))

        assert 'files' in cov
        assert 'test_it.py' in cov['files']
        test_cov = cov['files']['test_it.py']

        assert {1, 2, 3, 4}.issubset(set(test_cov['executed_lines']))
        assert set(test_cov['executed_lines']).issubset({1,2,3,4,5,6,7})
        assert [3,4] in test_cov['executed_branches']
        assert [3,-1] in test_cov['missing_branches']
