# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

"""Tests for coverage.pickle2json"""

from coverage.backward import pickle, iitems
from coverage.data import CoverageData
from coverage.pickle2json import pickle2json

from tests.coveragetest import CoverageTest
from tests.test_data import DataTestHelpers, LINES_1, ARCS_3


class Pickle2JsonTestInTempDir(DataTestHelpers, CoverageTest):
    """Tests pickle2json.py."""

    no_files_in_temp_dir = True

    def write_pickled_file(self, covdata, filename):
        """Write coverage data as pickled `filename`."""
        # Create the file data.
        file_data = {}

        if covdata._arcs:
            file_data['arcs'] = dict((f, list(amap)) for f, amap in iitems(covdata._arcs))
        else:
            file_data['lines'] = dict((f, list(lmap)) for f, lmap in iitems(covdata._lines))

        # Write the pickle to the file.
        with open(filename, 'wb') as file_obj:
            pickle.dump(file_data, file_obj, 2)

    def test_read_write_lines_pickle(self):
        # Test the old pickle format.
        covdata1 = CoverageData()
        covdata1.add_lines(LINES_1)
        self.write_pickled_file(covdata1, "lines.pkl")

        pickle2json("lines.pkl", "lines.json")

        covdata2 = CoverageData()
        covdata2.read_file("lines.json")
        self.assert_lines1_data(covdata2)

    def test_read_write_arcs_pickle(self):
        # Test the old pickle format.
        covdata1 = CoverageData()
        covdata1.add_arcs(ARCS_3)
        self.write_pickled_file(covdata1, "arcs.pkl")

        pickle2json("arcs.pkl", "arcs.json")

        covdata2 = CoverageData()
        covdata2.read_file("arcs.json")
        self.assert_arcs3_data(covdata2)
