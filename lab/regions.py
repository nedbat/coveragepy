"""
A quick hack to identify classes/functions in source files.
"""

import ast
import dataclasses
import pathlib
import sys

from coverage import Coverage

@dataclasses.dataclass
class Context:
    kind: str
    name: str
    lines: set[int]

class RegionFinder(ast.NodeVisitor):
    def __init__(self):
        self.regions = {}
        self.context = []

    def parse_source(self, source):
        self.visit(ast.parse(source))

    def visit_FunctionDef(self, node):
        lines = set(range(node.body[0].lineno, node.body[-1].end_lineno + 1))
        prefix = ""
        if self.context and self.context[-1].kind == "class":
            self.context[-1].lines |= lines
            prefix = self.context[-1].name + "."
        self.regions[prefix + node.name] = lines
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.context.append(Context("class", node.name, set()))
        self.generic_visit(node)
        self.regions[node.name] = self.context.pop().lines


cov = Coverage()
cov.load()
covdata = cov.get_data()
for fname in covdata.measured_files():
    analysis = cov.analyze(fname)
    text = pathlib.Path(fname).read_text()
    rf = RegionFinder()
    rf.parse_source(text)
    for name in sorted(rf.regions):
        lines = rf.regions[name]
        region_analysis = analysis.narrow(lines)
        print(f"{name}: {region_analysis.numbers.pc_covered_str}")
