# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Tests of the helpers in goldtest.py"""

import os.path
import re

import pytest

from tests.coveragetest import CoverageTest, TESTS_DIR
from tests.goldtest import compare, gold_path
from tests.goldtest import contains, contains_any, contains_rx, doesnt_contain
from tests.helpers import os_sep, re_line, remove_tree

GOOD_GETTY = """\
Four score and seven years ago our fathers brought forth upon this continent, a
new nation, conceived in Liberty, and dedicated to the proposition that all men
are created equal.
11/19/9999, Gettysburg, Pennsylvania
"""

BAD_GETTY = """\
Five score and seven years ago our fathers brought forth upon this continent, a
new nation, conceived in Liberty, and dedicated to the proposition that all men
are created equal.
333:4444:55555, Gettysburg, Pennsylvania
"""

SCRUBS = [
    # Numbers don't matter when comparing.
    (r'\d+', 'D'),
    (r'[/:]', '-'),
]

def path_regex(path):
    return re.sub(r"[/\\]", r"[/\\\\]", path.replace(".", "[.]"))

ACTUAL_DIR = os.path.join(TESTS_DIR, "actual/testing/getty")
ACTUAL_GETTY_FILE = os.path.join(ACTUAL_DIR, "gettysburg.txt")
GOLD_GETTY_FILE = os.path.join(TESTS_DIR, "gold/testing/getty/gettysburg.txt")
GOLD_GETTY_FILE_RX = path_regex(GOLD_GETTY_FILE)

GOLD_PATH_RX = path_regex("/tests/gold/testing/getty/gettysburg.txt")
OUT_PATH_RX = path_regex("out/gettysburg.txt")

class CompareTest(CoverageTest):
    """Tests of goldtest.py:compare()"""

    def setup_test(self):
        super().setup_test()
        self.addCleanup(remove_tree, ACTUAL_DIR)

    def test_good(self):
        self.make_file("out/gettysburg.txt", GOOD_GETTY)
        compare(gold_path("testing/getty"), "out", scrubs=SCRUBS)
        self.assert_doesnt_exist(ACTUAL_GETTY_FILE)

    def test_bad(self):
        self.make_file("out/gettysburg.txt", BAD_GETTY)

        # compare() raises an assertion.
        msg = rf"Files differ: .*{GOLD_PATH_RX} != {OUT_PATH_RX}"
        with pytest.raises(AssertionError, match=msg):
            compare(gold_path("testing/getty"), "out", scrubs=SCRUBS)

        # Stdout has a description of the diff.  The diff shows the scrubbed content.
        stdout = self.stdout()
        assert "- Four score" in stdout
        assert "+ Five score" in stdout
        assert re_line(stdout, rf"^:::: diff '.*{GOLD_PATH_RX}' and '{OUT_PATH_RX}'")
        assert re_line(stdout, rf"^:::: end diff '.*{GOLD_PATH_RX}' and '{OUT_PATH_RX}'")
        assert "  D-D-D, Gettysburg, Pennsylvania" in stdout

        # The actual file was saved.
        with open(ACTUAL_GETTY_FILE) as f:
            saved = f.read()
        assert saved == BAD_GETTY

    def test_good_needs_scrubs(self):
        # Comparing the "good" result without scrubbing the variable parts will fail.
        self.make_file("out/gettysburg.txt", GOOD_GETTY)

        # compare() raises an assertion.
        msg = rf"Files differ: .*{GOLD_PATH_RX} != {OUT_PATH_RX}"
        with pytest.raises(AssertionError, match=msg):
            compare(gold_path("testing/getty"), "out")

        stdout = self.stdout()
        assert "- 11/19/1863, Gettysburg, Pennsylvania" in stdout
        assert "+ 11/19/9999, Gettysburg, Pennsylvania" in stdout

    def test_actual_extra(self):
        self.make_file("out/gettysburg.txt", GOOD_GETTY)
        self.make_file("out/another.more", "hi")

        # Extra files in the output are ok with actual_extra=True.
        compare(gold_path("testing/getty"), "out", scrubs=SCRUBS, actual_extra=True)

        # But not without it:
        msg = r"Files in out only: \['another.more'\]"
        with pytest.raises(AssertionError, match=msg):
            compare(gold_path("testing/getty"), "out", scrubs=SCRUBS)
        self.assert_exists(os.path.join(TESTS_DIR, "actual/testing/getty/another.more"))

        # But only the files matching the file_pattern are considered.
        compare(gold_path("testing/getty"), "out", file_pattern="*.txt", scrubs=SCRUBS)

    def test_xml(self):
        self.make_file("out/output.xml", """\
            <?xml version="1.0" ?>
            <the_root c="3" b="2" a="1">
                <also z="9" x="7" y="8">
                    Hello
                </also>
            </the_root>
            """)
        compare(gold_path("testing/xml"), "out")


class ContainsTest(CoverageTest):
    """Tests of the various "contains" functions in goldtest.py"""

    run_in_temp_dir = False

    def test_contains(self):
        contains(GOLD_GETTY_FILE, "Four", "fathers", "dedicated")
        msg = rf"Missing content in {GOLD_GETTY_FILE_RX}: 'xyzzy'"
        with pytest.raises(AssertionError, match=msg):
            contains(GOLD_GETTY_FILE, "Four", "fathers", "xyzzy", "dedicated")

    def test_contains_rx(self):
        contains_rx(GOLD_GETTY_FILE, r"Fo.r", r"f[abc]thers", "dedi[cdef]ated")
        msg = rf"Missing regex in {GOLD_GETTY_FILE_RX}: r'm\[opq\]thers'"
        with pytest.raises(AssertionError, match=msg):
            contains_rx(GOLD_GETTY_FILE, r"Fo.r", r"m[opq]thers")

    def test_contains_any(self):
        contains_any(GOLD_GETTY_FILE, "Five", "Four", "Three")
        msg = rf"Missing content in {GOLD_GETTY_FILE_RX}: 'One' \[1 of 3\]"
        with pytest.raises(AssertionError, match=msg):
            contains_any(GOLD_GETTY_FILE, "One", "Two", "Three")

    def test_doesnt_contain(self):
        doesnt_contain(GOLD_GETTY_FILE, "One", "Two", "Three")
        msg = rf"Forbidden content in {GOLD_GETTY_FILE_RX}: 'Four'"
        with pytest.raises(AssertionError, match=msg):
            doesnt_contain(GOLD_GETTY_FILE, "Three", "Four", "Five")
