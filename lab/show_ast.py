# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Dump the AST of a file."""

import ast
import sys

from coverage.parser import ast_dump

ast_dump(ast.parse(open(sys.argv[1], "rb").read()))
