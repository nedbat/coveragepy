"""Tests for coverage.data"""

import cPickle as pickle
from coverage.data import CoverageData
from coveragetest import CoverageTest


DATA_1 = [ ('a.py',1), ('a.py',2), ('b.py',3) ]
SUMMARY_1 = { 'a.py':2, 'b.py':1 }
EXECED_FILES_1 = [ 'a.py', 'b.py' ]
A_PY_LINES_1 = [1,2]
B_PY_LINES_1 = [3]

DATA_2 = [ ('a.py',1), ('a.py',5), ('c.py',17) ]
SUMMARY_1_2 = { 'a.py':3, 'b.py':1, 'c.py':1 }
EXECED_FILES_1_2 = [ 'a.py', 'b.py', 'c.py' ]


class DataTest(CoverageTest):
    
    def assert_summary(self, covdata, summary):
        self.assertEqual(covdata.summary(), summary)
        
    def assert_executed_files(self, covdata, execed):
        self.assert_equal_sets(covdata.executed_files(), execed)
    
    def test_reading_empty(self):
        covdata = CoverageData()
        covdata.read()
        self.assert_summary(covdata, {})

    def test_adding_data(self):
        covdata = CoverageData()
        covdata.add_line_data(DATA_1)
        self.assert_summary(covdata, SUMMARY_1)
        self.assert_executed_files(covdata, EXECED_FILES_1)
        
    def test_writing_and_reading(self):
        covdata1 = CoverageData()
        covdata1.add_line_data(DATA_1)
        covdata1.write()
        
        covdata2 = CoverageData()
        covdata2.read()
        self.assert_summary(covdata2, SUMMARY_1)

    def test_combining(self):
        covdata1 = CoverageData()
        covdata1.set_suffix('1')
        covdata1.add_line_data(DATA_1)
        covdata1.write()
        
        covdata2 = CoverageData()
        covdata2.set_suffix('2')
        covdata2.add_line_data(DATA_2)
        covdata2.write()
        
        covdata3 = CoverageData()
        covdata3.combine_parallel_data()
        self.assert_summary(covdata3, SUMMARY_1_2)
        self.assert_executed_files(covdata3, EXECED_FILES_1_2)

    def test_erasing(self):
        covdata1 = CoverageData()
        covdata1.add_line_data(DATA_1)
        covdata1.write()
        covdata1.erase()
        self.assert_summary(covdata1, {})
        
        covdata2 = CoverageData()
        covdata2.read()
        self.assert_summary(covdata2, {})

    def test_file_format(self):
        # Write with CoverageData, then read the pickle explicitly.
        covdata = CoverageData()
        covdata.add_line_data(DATA_1)
        covdata.write()
        
        fdata = open(".coverage", 'rb')
        try:
            data = pickle.load(fdata)
        finally:
            fdata.close()
        
        lines = data['lines']
        self.assert_equal_sets(lines.keys(), EXECED_FILES_1)
        self.assert_equal_sets(lines['a.py'], A_PY_LINES_1)
        self.assert_equal_sets(lines['b.py'], B_PY_LINES_1)
