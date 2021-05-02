"""Generate random Python for testing."""

import collections
from itertools import cycle, product
import random
import re

from coverage.parser import PythonParser


class PythonSpinner:
    """Spin Python source from a simple AST."""

    def __init__(self):
        self.lines = []
        self.lines.append("async def func():")
        self.indent = 4

    @property
    def lineno(self):
        return len(self.lines) + 1

    @classmethod
    def generate_python(cls, ast):
        spinner = cls()
        spinner.gen_python_internal(ast)
        return "\n".join(spinner.lines)

    def add_line(self, line):
        g = f"g{self.lineno}"
        self.lines.append(' ' * self.indent + line.format(g=g, lineno=self.lineno))

    def add_block(self, node):
        self.indent += 4
        self.gen_python_internal(node)
        self.indent -= 4

    def maybe_block(self, node, nodei, keyword):
        if len(node) > nodei and node[nodei] is not None:
            self.add_line(keyword + ":")
            self.add_block(node[nodei])

    def gen_python_internal(self, ast):
        for node in ast:
            if isinstance(node, list):
                op = node[0]
                if op == "if":
                    self.add_line("if {g}:")
                    self.add_block(node[1])
                    self.maybe_block(node, 2, "else")
                elif op == "for":
                    self.add_line("for x in {g}:")
                    self.add_block(node[1])
                    self.maybe_block(node, 2, "else")
                elif op == "while":
                    self.add_line("while {g}:")
                    self.add_block(node[1])
                    self.maybe_block(node, 2, "else")
                elif op == "try":
                    self.add_line("try:")
                    self.add_block(node[1])
                    # 'except' clauses are different, because there can be any
                    # number.
                    if len(node) > 2 and node[2] is not None:
                        for except_node in node[2]:
                            self.add_line(f"except Exception{self.lineno}:")
                            self.add_block(except_node)
                    self.maybe_block(node, 3, "else")
                    self.maybe_block(node, 4, "finally")
                elif op == "with":
                    self.add_line("with {g} as x:")
                    self.add_block(node[1])
                else:
                    raise Exception(f"Bad list node: {node!r}")
            else:
                op = node
                if op == "assign":
                    self.add_line("x = {lineno}")
                elif op in ["break", "continue"]:
                    self.add_line(op)
                elif op == "return":
                    self.add_line("return")
                elif op == "yield":
                    self.add_line("yield {lineno}")
                else:
                    raise Exception(f"Bad atom node: {node!r}")


def weighted_choice(rand, choices):
    """Choose from a list of [(choice, weight), ...] options, randomly."""
    total = sum(w for c, w in choices)
    r = rand.uniform(0, total)
    upto = 0
    for c, w in choices:
        if upto + w >= r:
            return c
        upto += w
    assert False, "Shouldn't get here"


class RandomAstMaker:
    def __init__(self, seed=None):
        self.r = random.Random()
        if seed is not None:
            self.r.seed(seed)
        self.depth = 0
        self.bc_allowed = set()

    def roll(self, prob=0.5):
        return self.r.random() <= prob

    def choose(self, choices):
        """Roll the dice to choose an option."""
        return weighted_choice(self.r, choices)

    STMT_CHOICES = [
        [("if", 10), ("for", 10), ("try", 10), ("while", 3), ("with", 10), ("assign", 20), ("return", 1), ("yield", 0)],
        [("if", 10), ("for", 10), ("try", 10), ("while", 3), ("with", 10), ("assign", 40), ("return", 1), ("yield", 0), ("break", 10), ("continue", 10)],
        [("if", 10), ("for", 10), ("try", 10), ("while", 3), ("with", 10), ("assign", 40), ("return", 1), ("yield", 0), ("break", 10), ("continue", 10)],
        [("if", 10), ("for", 10), ("try", 10), ("while", 3), ("with", 10), ("assign", 40), ("return", 1), ("yield", 0), ("break", 10), ("continue", 10)],
        [("if", 10), ("for", 10), ("try", 10), ("while", 3), ("with", 10), ("assign", 40), ("return", 1), ("yield", 0), ("break", 10), ("continue", 10)],
        # Last element has to have no compound statements, to limit depth.
        [("assign", 10), ("return", 1), ("yield", 0), ("break", 10), ("continue", 10)],
    ]

    def make_body(self, parent):
        body = []
        choices = self.STMT_CHOICES[self.depth]

        self.depth += 1
        nstmts = self.choose([(1, 10), (2, 25), (3, 10), (4, 10), (5, 5)])
        for _ in range(nstmts):
            stmt = self.choose(choices)
            if stmt == "if":
                body.append(["if", self.make_body("if")])
                if self.roll():
                    body[-1].append(self.make_body("ifelse"))
            elif stmt == "for":
                old_allowed = self.bc_allowed
                self.bc_allowed = self.bc_allowed | {"break", "continue"}
                body.append(["for", self.make_body("for")])
                self.bc_allowed = old_allowed
                if self.roll():
                    body[-1].append(self.make_body("forelse"))
            elif stmt == "while":
                old_allowed = self.bc_allowed
                self.bc_allowed = self.bc_allowed | {"break", "continue"}
                body.append(["while", self.make_body("while")])
                self.bc_allowed = old_allowed
                if self.roll():
                    body[-1].append(self.make_body("whileelse"))
            elif stmt == "try":
                else_clause = self.make_body("try") if self.roll() else None
                old_allowed = self.bc_allowed
                self.bc_allowed = self.bc_allowed - {"continue"}
                finally_clause = self.make_body("finally") if self.roll() else None
                self.bc_allowed = old_allowed
                if else_clause:
                    with_exceptions = True
                elif not else_clause and not finally_clause:
                    with_exceptions = True
                else:
                    with_exceptions = self.roll()
                if with_exceptions:
                    num_exceptions = self.choose([(1, 50), (2, 50)])
                    exceptions = [self.make_body("except") for _ in range(num_exceptions)]
                else:
                    exceptions = None
                body.append(
                    ["try", self.make_body("tryelse"), exceptions, else_clause, finally_clause]
                )
            elif stmt == "with":
                body.append(["with", self.make_body("with")])
            elif stmt == "return":
                body.append(stmt)
                break
            elif stmt == "yield":
                body.append("yield")
            elif stmt in ["break", "continue"]:
                if stmt in self.bc_allowed:
                    # A break or continue immediately after a loop is not
                    # interesting.  So if we are immediately after a loop, then
                    # insert an assignment.
                    if not body and (parent in ["for", "while"]):
                        body.append("assign")
                    body.append(stmt)
                    break
                else:
                    stmt = "assign"

            if stmt == "assign":
                # Don't put two assignments in a row, there's no point.
                if not body or body[-1] != "assign":
                    body.append("assign")

        self.depth -= 1
        return body


def async_alternatives(source):
    parts = re.split(r"(for |with )", source)
    nchoices = len(parts) // 2
    #print("{} choices".format(nchoices))

    def constant(s):
        return [s]

    def maybe_async(s):
        return [s, "async "+s]

    choices = [f(x) for f, x in zip(cycle([constant, maybe_async]), parts)]
    for result in product(*choices):
        source = "".join(result)
        yield source


def compare_alternatives(source):
    all_all_arcs = collections.defaultdict(list)
    for i, alternate_source in enumerate(async_alternatives(source)):
        parser = PythonParser(alternate_source)
        arcs = parser.arcs()
        all_all_arcs[tuple(arcs)].append((i, alternate_source))

    return len(all_all_arcs)


def show_a_bunch():
    longest = ""
    for i in range(100):
        maker = RandomAstMaker(i)
        source = PythonSpinner.generate_python(maker.make_body("def"))
        try:
            print("-"*80, "\n", source, sep="")
            compile(source, "<string>", "exec")
        except Exception as ex:
            print(f"Oops: {ex}\n{source}")
        if len(source) > len(longest):
            longest = source


def show_alternatives():
    for i in range(1000):
        maker = RandomAstMaker(i)
        source = PythonSpinner.generate_python(maker.make_body("def"))
        nlines = len(source.splitlines())
        if nlines < 15:
            nalt = compare_alternatives(source)
            if nalt > 1:
                print(f"--- {nlines:3} lines, {nalt:2} alternatives ---------")
                print(source)



def show_one():
    maker = RandomAstMaker()
    source = PythonSpinner.generate_python(maker.make_body("def"))
    print(source)

if __name__ == "__main__":
    show_one()
    #show_alternatives()
