# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

"""Tests of coverage/python.py"""

import os
import sys
from coverage import env

from coverage.python import get_zip_bytes, source_for_file

from tests.coveragetest import CoverageTest


class GetZipBytesTest(CoverageTest):
    """Tests of `get_zip_bytes`."""

    run_in_temp_dir = False

    def test_get_encoded_zip_files(self):
        # See igor.py, do_zipmods, for the text of these files.
        zip_file = "tests/zipmods.zip"
        sys.path.append(zip_file)       # So we can import the files.
        for encoding in ["utf8", "gb2312", "hebrew", "shift_jis", "cp1252"]:
            filename = zip_file + "/encoded_" + encoding + ".py"
            filename = filename.replace("/", os.sep)
            zip_data = get_zip_bytes(filename)
            zip_text = zip_data.decode(encoding)
            self.assertIn('All OK', zip_text)
            # Run the code to see that we really got it encoded properly.
            __import__("encoded_"+encoding)

def test_source_for_file(tmpdir):
    path = tmpdir.join("a.py")
    src = str(path)
    assert src == source_for_file(src)
    assert src == source_for_file(src + 'c')
    assert src == source_for_file(src + 'o')
    unknown = src + 'FOO'
    assert unknown == source_for_file(unknown)
    #
    # On windows if a pyw exists, it is an acceptable source
    #
    windows = env.WINDOWS
    env.WINDOWS = True
    path_windows = tmpdir.ensure("a.pyw")
    assert str(path_windows) == source_for_file(src + 'c')
    #
    # If both pyw and py exist, py is preferred
    #
    path.ensure(file=True)
    assert src == source_for_file(src + 'c')
    env.WINDOWS = windows
    jython_src = "a"
    assert jython_src + ".py" == source_for_file(jython_src + "$py.class")
