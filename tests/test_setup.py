# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Tests of miscellaneous stuff."""

import sys

import coverage

from tests.coveragetest import CoverageTest


class SetupPyTest(CoverageTest):
    """Tests of setup.py"""

    run_in_temp_dir = False

    def setUp(self):
        super().setUp()
        # Force the most restrictive interpretation.
        self.set_environ('LC_ALL', 'C')

    def test_metadata(self):
        status, output = self.run_command_status(
            "python setup.py --description --version --url --author"
        )
        assert status == 0
        out = output.splitlines()
        assert "measurement" in out[0]
        assert coverage.__version__ == out[1]
        assert "github.com/nedbat/coveragepy" in out[2]
        assert "Ned Batchelder" in out[3]

    def test_more_metadata(self):
        # Let's be sure we pick up our own setup.py
        # CoverageTest restores the original sys.path for us.
        sys.path.insert(0, '')
        from setup import setup_args

        classifiers = setup_args['classifiers']
        assert len(classifiers) > 7
        assert classifiers[-1].startswith("Development Status ::")
        assert "Programming Language :: Python :: %d" % sys.version_info[:1] in classifiers
        assert "Programming Language :: Python :: %d.%d" % sys.version_info[:2] in classifiers

        long_description = setup_args['long_description'].splitlines()
        assert len(long_description) > 7
        assert long_description[0].strip() != ""
        assert long_description[-1].strip() != ""
