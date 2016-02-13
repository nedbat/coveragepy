"""Parse every Python file in a tree."""

import os
import sys

from coverage.misc import CoverageException
from coverage.parser import PythonParser

for root, dirnames, filenames in os.walk(sys.argv[1]):
    for filename in filenames:
        if filename.endswith(".py"):
            filename = os.path.join(root, filename)
            print(":: {}".format(filename))
            try:
                par = PythonParser(filename=filename)
                par.parse_source()
                par.arcs()
            except Exception as exc:
                print("  ** {}".format(exc))
