# Run some timing tests of JsonData vs SqliteData.

import random
import time

from coverage.data import CoverageJsonData
from coverage.sqldata import CoverageSqliteData

NUM_FILES = 1000
NUM_LINES = 1000

def gen_data(cdata):
    rnd = random.Random()
    rnd.seed(17)

    def linenos(num_lines, prob):
        return (n for n in range(num_lines) if random.random() < prob)

    start = time.time()
    for i in range(NUM_FILES):
        filename = "/src/foo/project/file{i}.py".format(i=i)
        line_data = { filename: dict.fromkeys(linenos(NUM_LINES, .6)) }
        cdata.add_lines(line_data)

    cdata.write()
    end = time.time()
    delta = end - start
    return delta

class DummyData:
    def add_lines(self, line_data):
        return
    def write(self):
        return

overhead = gen_data(DummyData())
jtime = gen_data(CoverageJsonData("gendata.json")) - overhead
stime = gen_data(CoverageSqliteData("gendata.db")) - overhead
print("Overhead: {overhead:.3f}s".format(overhead=overhead))
print("JSON: {jtime:.3f}s".format(jtime=jtime))
print("SQLite: {stime:.3f}s".format(stime=stime))
print("{slower:.3f}x slower".format(slower=stime/jtime))
