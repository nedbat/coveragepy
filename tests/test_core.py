# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/coveragepy/coveragepy/blob/main/NOTICE.txt

"""Tests for core selection of coverage.py."""

from __future__ import annotations

import pytest

import coverage
from coverage import env
from coverage.exceptions import ConfigError

from tests.coveragetest import CoverageTest
from tests.helpers import re_line, re_lines


class CoverageCoreTest(CoverageTest):
    """Test that cores are chosen correctly."""

    # This doesn't test failure modes, only successful requests.
    try:
        from coverage.tracer import CTracer

        has_ctracer = True
    except ImportError:
        has_ctracer = False

    def setUp(self) -> None:
        super().setUp()
        # Clean out the environment variable the test suite uses to control the
        # core it cares about.
        self.del_environ("COVERAGE_CORE")
        self.make_file("numbers.py", "print(123, 456)")

    def test_core_default(self) -> None:
        out = self.run_command("coverage run --debug=sys numbers.py")
        assert out.endswith("123 456\n")
        core = re_line(r" core:", out).strip()
        warns = re_lines(r"\(no-ctracer\)", out)
        if env.SYSMON_DEFAULT:
            assert core == "core: SysMonitor"
            assert not warns
        elif self.has_ctracer:
            assert core == "core: CTracer"
            assert not warns
        else:
            assert core == "core: PyTracer"
            assert bool(warns) == env.CPYTHON

    @pytest.mark.skipif(not has_ctracer, reason="No CTracer to request")
    def test_core_request_ctrace(self) -> None:
        self.set_environ("COVERAGE_CORE", "ctrace")
        out = self.run_command("coverage run --debug=sys numbers.py")
        assert out.endswith("123 456\n")
        core = re_line(r" core:", out).strip()
        assert core == "core: CTracer"

    @pytest.mark.skipif(has_ctracer, reason="CTracer needs to be missing")
    def test_core_request_ctrace_but_missing(self) -> None:
        self.make_file(".coveragerc", "[run]\ncore = ctrace\n")
        out = self.run_command("coverage run --debug=sys,pybehave numbers.py")
        assert out.endswith("123 456\n")
        core = re_line(r" core:", out).strip()
        assert core == "core: PyTracer"
        warns = re_lines(r"\(no-ctracer\)", out)
        assert bool(warns) == env.SHIPPING_WHEELS

    def test_core_request_pytrace(self) -> None:
        self.set_environ("COVERAGE_CORE", "pytrace")
        out = self.run_command("coverage run --debug=sys numbers.py")
        assert out.endswith("123 456\n")
        core = re_line(r" core:", out).strip()
        assert core == "core: PyTracer"

    def test_core_request_sysmon(self) -> None:
        self.set_environ("COVERAGE_CORE", "sysmon")
        if env.PYBEHAVIOR.pep669:
            status = 0
        else:
            status = 1
        out = self.run_command("coverage run --debug=sys numbers.py", status=status)
        if status == 0:
            assert out.endswith("123 456\n")
            core = re_line(r" core:", out).strip()
            assert core == "core: SysMonitor"
        else:
            assert "Can't use core=sysmon: sys.monitoring isn't available in this version;" in out

    def test_core_request_sysmon_no_dyncontext(self) -> None:
        # Use config core= for this test just to be different.
        self.make_file(
            ".coveragerc",
            """\
            [run]
            core = sysmon
            dynamic_context = test_function
            """,
        )
        out = self.run_command("coverage run --debug=sys numbers.py", status=1)
        if env.PYBEHAVIOR.pep669:
            assert "Can't use core=sysmon: it doesn't yet support dynamic contexts;" in out
        else:
            assert "Can't use core=sysmon: sys.monitoring isn't available in this version;" in out

    def test_core_request_sysmon_no_branches(self) -> None:
        # Use config core= for this test just to be different.
        self.make_file(
            ".coveragerc",
            """\
            [run]
            core = sysmon
            branch = True
            """,
        )
        if env.PYBEHAVIOR.branch_right_left:
            status = 0
        elif env.PYBEHAVIOR.pep669:
            status = 1
            msg = "Can't use core=sysmon: sys.monitoring can't measure branches in this version;"
        else:
            status = 1
            msg = "Can't use core=sysmon: sys.monitoring isn't available in this version;"
        out = self.run_command("coverage run --debug=sys numbers.py", status=status)
        if status == 0:
            assert out.endswith("123 456\n")
            core = re_line(r" core:", out).strip()
            assert core == "core: SysMonitor"
        else:
            assert msg in out  # pylint: disable=possibly-used-before-assignment

    def test_core_request_nosuchcore(self) -> None:
        # Test the coverage misconfigurations in-process with pytest. Running a
        # subprocess doesn't capture the metacov in the subprocess because
        # coverage is misconfigured.
        self.set_environ("COVERAGE_CORE", "nosuchcore")
        cov = coverage.Coverage()
        with pytest.raises(ConfigError, match=r"Unknown core value: 'nosuchcore'"):
            self.start_import_stop(cov, "numbers")
