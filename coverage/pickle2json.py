# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

"""Convert pickle to JSON for coverage.py."""

from coverage.backward import pickle
from coverage.data import CoverageData

def pickle_read_raw_data(cls, file_obj):
    return pickle.load(file_obj)

def pickle2json(infile, outfile):
    try:
        old_read_raw_data = CoverageData._read_raw_data
        CoverageData._read_raw_data = pickle_read_raw_data

        covdata = CoverageData()

        inf = open(infile, 'rb')
        covdata.read(inf)
        inf.close()

        covdata.write_file(outfile)
    finally:
        CoverageData._read_raw_data = old_read_raw_data


if __name__ == "__main__":
    from optparse import OptionParser

    parser = OptionParser(usage="usage: %s [options]" % __file__)
    parser.description = "Convert .coverage files from pickle to JSON format"
    parser.add_option("-i", "--input-file", action="store", default=".coverage",
                        help="Name of input file. Default .coverage")
    parser.add_option("-o", "--output-file", action="store", default=".coverage",
                        help="Name of output file. Default .coverage")

    (options, args) = parser.parse_args()

    pickle2json(options.input_file, options.output_file)
