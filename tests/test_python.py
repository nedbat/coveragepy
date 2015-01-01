"""Tests of coverage/python.py"""

import os
import sys

from coverage.python import get_zip_bytes

from tests.coveragetest import CoverageTest


class GetZipBytesTest(CoverageTest):
    """Tests of `get_zip_bytes`."""

    run_in_temp_dir = False

    def test_get_encoded_zip_files(self):
        # See igor.py, do_zipmods, for the text of these files.
        zip_file = "tests/zipmods.zip"
        sys.path.append(zip_file)       # So we can import the files.
        for encoding in ["utf8", "gb2312", "hebrew", "shift_jis"]:
            filename = zip_file + "/encoded_" + encoding + ".py"
            filename = filename.replace("/", os.sep)
            zip_data = get_zip_bytes(filename)
            zip_text = zip_data.decode(encoding)
            self.assertIn('All OK', zip_text)
            # Run the code to see that we really got it encoded properly.
            __import__("encoded_"+encoding)
