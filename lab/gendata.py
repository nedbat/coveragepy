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
        filename = f"/src/foo/project/file{i}.py"
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
print(f"Overhead: {overhead:.3f}s")
print(f"JSON: {jtime:.3f}s")
print(f"SQLite: {stime:.3f}s")
print(f"{stime / jtime:.3f}x slower")
