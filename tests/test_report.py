# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Tests for helpers in report.py"""

import pytest

from coverage.exceptions import CoverageException
from coverage.report import render_report
from tests.coveragetest import CoverageTest


class FakeReporter:
    """A fake implementation of a one-file reporter."""

    report_type = "fake report file"

    def __init__(self, output="", error=False):
        self.output = output
        self.error = error
        self.morfs = None

    def report(self, morfs, outfile):
        """Fake."""
        self.morfs = morfs
        outfile.write(self.output)
        if self.error:
            raise CoverageException("You asked for it!")


class RenderReportTest(CoverageTest):
    """Tests of render_report."""

    def test_stdout(self):
        fake = FakeReporter(output="Hello!\n")
        msgs = []
        render_report("-", fake, [pytest, "coverage"], msgs.append)
        assert fake.morfs == [pytest, "coverage"]
        assert self.stdout() == "Hello!\n"
        assert not msgs

    def test_file(self):
        fake = FakeReporter(output="Gréètings!\n")
        msgs = []
        render_report("output.txt", fake, [], msgs.append)
        assert self.stdout() == ""
        with open("output.txt", "rb") as f:
            assert f.read().rstrip() == b"Gr\xc3\xa9\xc3\xa8tings!"
        assert msgs == ["Wrote fake report file to output.txt"]

    def test_exception(self):
        fake = FakeReporter(error=True)
        msgs = []
        with pytest.raises(CoverageException, match="You asked for it!"):
            render_report("output.txt", fake, [], msgs.append)
        assert self.stdout() == ""
        self.assert_doesnt_exist("output.txt")
        assert not msgs
