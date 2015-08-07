# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

"""Tests for coverage.pickle2json"""

from coverage.backward import pickle, iitems
from coverage.data import CoverageData
from coverage.pickle2json import pickle2json

from tests.coveragetest import CoverageTest
from tests.test_data import *

class Pickle2JsonTestInTempDir(DataTestHelpers, CoverageTest):
    """ Tests pickle2json """

    def write_pickled_file(self, covdata, filename):
        """ write coverage data as pickled `filename` """
        # Create the file data.
        file_data = {}

        if covdata._arcs:
            file_data['arcs'] = dict((f, list(amap)) for f, amap in iitems(covdata._arcs))
        else:
            file_data['lines'] = dict((f, list(lmap)) for f, lmap in iitems(covdata._lines))

        # Write the pickle to the file.
        file_obj = open(filename, 'wb')
        try:
            pickle.dump(file_data, file_obj, 2)
        finally:
            file_obj.close()

    def test_read_write_lines_pickle(self):
        """ test the old pickle format """
        covdata1 = CoverageData()
        covdata1.set_lines(LINES_1)
        self.write_pickled_file(covdata1, "lines.pkl")

        pickle2json("lines.pkl", "lines.json")

        covdata2 = CoverageData()
        covdata2.read_file("lines.json")
        self.assert_line_counts(covdata2, SUMMARY_1)
        self.assert_measured_files(covdata2, MEASURED_FILES_1)
        self.assertCountEqual(covdata2.lines("a.py"), A_PY_LINES_1)
        self.assertEqual(covdata2.run_infos(), [])

    def test_read_write_arcs_pickle(self):
        """ test the old pickle format """
        covdata1 = CoverageData()
        covdata1.set_arcs(ARCS_3)
        self.write_pickled_file(covdata1, "arcs.pkl")

        pickle2json("arcs.pkl", "arcs.json")

        covdata2 = CoverageData()
        covdata2.read_file("arcs.json")
        self.assert_line_counts(covdata2, SUMMARY_3)
        self.assert_measured_files(covdata2, MEASURED_FILES_3)
        self.assertCountEqual(covdata2.lines("x.py"), X_PY_LINES_3)
        self.assertCountEqual(covdata2.arcs("x.py"), X_PY_ARCS_3)
        self.assertCountEqual(covdata2.lines("y.py"), Y_PY_LINES_3)
        self.assertCountEqual(covdata2.arcs("y.py"), Y_PY_ARCS_3)
        self.assertEqual(covdata2.run_infos(), [])
