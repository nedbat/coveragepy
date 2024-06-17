# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""
Instrument source code for sys.monitoring.

Based on Slipcover's branch.py under the Apache license:
https://github.com/plasma-umass/slipcover/blob/28c637a786f938135ee8ffe7c4a1c788e13d92fa/src/slipcover/branch.py

Many thanks to Juan Altmayer Pizzorno and Emery Berger.

"""

from __future__ import annotations

import ast
import sys


FROM_DIGITS = 4
TO_DIGITS = 4
JUMP = 1 * 10 ** (FROM_DIGITS + TO_DIGITS)

def is_branch(lineno):
    return lineno > 10 ** (FROM_DIGITS + TO_DIGITS)

def encode_branch(from_line, to_line):
    # FIXME anything bigger, and we get an overflow... encode to_line as relative number?
    # assert from_line <= 0x7FFF, f"Line number {from_line} too high, unable to add branch tracking"
    # assert to_line <= 0x7FFF, f"Line number {to_line} too high, unable to add branch tracking"
    #return (1<<30)|((from_line & 0x7FFF)<<15)|(to_line&0x7FFF)
    return JUMP + (from_line * 10 ** TO_DIGITS) + to_line

def decode_branch(lineno):
    return (
        (lineno // 10 ** TO_DIGITS) % 10 ** FROM_DIGITS,
        lineno % (10 ** TO_DIGITS),
    )

class FakeBranchLineTransformer(ast.NodeTransformer):

    def _mark_branch(self, from_lineno: int, to_lineno: int) -> list[ast.stmt]:
        mark = ast.Expr(ast.Constant(1723))
        #assert sys.version_info[0:2] >= (3,12)
        for node in ast.walk(mark):
            node.lineno = node.end_lineno = encode_branch(from_lineno, to_lineno)
            # Leaving the columns unitialized can lead to invalid positions despite
            # our use of ast.fix_missing_locations
            node.col_offset = node.end_col_offset = -1

        return [mark]

    def visit_FunctionDef(self, node: ast.AsyncFunctionDef | ast.FunctionDef) -> ast.AST:
        super().generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        return self.visit_FunctionDef(node)

    def _mark_branches(self, node: ast.AST) -> ast.AST:
        node.body = self._mark_branch(node.lineno, node.body[0].lineno) + node.body

        if node.orelse:
            node.orelse = self._mark_branch(node.lineno, node.orelse[0].lineno) + node.orelse
        else:
            to_line = node.next_node.lineno if node.next_node else 0 # exit
            node.orelse = self._mark_branch(node.lineno, to_line)

        super().generic_visit(node)
        return node

    def visit_If(self, node: ast.If) -> ast.AST:
        return self._mark_branches(node)

    def visit_For(self, node: ast.For) -> ast.AST:
        return self._mark_branches(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> ast.AST:
        return self._mark_branches(node)

    def visit_While(self, node: ast.While) -> ast.AST:
        return self._mark_branches(node)

    def visit_Match(self, node: ast.Match) -> ast.Match:
        for case in node.cases:
            case.body = self._mark_branch(node.lineno, case.body[0].lineno) + case.body

        pattern = node.cases[-1].pattern
        while isinstance(pattern, ast.MatchOr):
            pattern = pattern.patterns[-1]
        has_wildcard = isinstance(pattern, ast.MatchAs)

        if not has_wildcard:
            to_line = node.next_node.lineno if node.next_node else 0 # exit
            node.cases.append(ast.match_case(ast.MatchAs(),
                                             body=self._mark_branch(node.lineno, to_line)))

        super().generic_visit(node)
        return node


def compile_instrumented(source: str, filename: str): # -> code object
    tree = ast.parse(source)

    match_type = ast.Match if sys.version_info >= (3,10) else tuple() # empty tuple matches nothing
    try_type = (ast.Try, ast.TryStar) if sys.version_info >= (3,11) else ast.Try

    # Compute the "next" statement in case a branch flows control out of a node.
    # We need a parent node's "next" computed before its siblings, so we compute it here, in BFS;
    # note that visit() doesn't guarantee any specific order.
    tree.next_node = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # no next node, yields (..., 0), i.e., "->exit" branch
            node.next_node = None

        for name, field in ast.iter_fields(node):
            if isinstance(field, ast.AST):
                # if a field is just a node, any execution continues after our node
                field.next_node = node.next_node
            elif isinstance(node, match_type) and name == 'cases':
                # each case continues after the 'match'
                for item in field:
                    item.next_node = node.next_node
            elif isinstance(node, try_type) and name == 'handlers':
                # each 'except' continues either in 'finally', or after the 'try'
                for h in field:
                    h.next_node = node.finalbody[0] if node.finalbody else node.next_node
            elif isinstance(field, list):
                # if a field is a list, each item but the last one continues with the next item
                prev = None
                for item in field:
                    if isinstance(item, ast.AST):
                        if prev:
                            prev.next_node = item
                        prev = item

                if prev:
                    if isinstance(node, (ast.For, ast.While)):
                        prev.next_node = node   # loops back
                    elif isinstance(node, try_type) and (name in ('body', 'orelse')):
                        if name == 'body' and node.orelse:
                            prev.next_node = node.orelse[0]
                        elif node.finalbody:
                            prev.next_node = node.finalbody[0]
                        else:
                            prev.next_node = node.next_node
                    else:
                        prev.next_node = node.next_node

    tree = FakeBranchLineTransformer().visit(tree)
    ast.fix_missing_locations(tree)
    import contextlib, os
    with open("/tmp/foo.out", "a") as f:
        with contextlib.redirect_stdout(f):
            print("=" * 80)
            print(f"--- test: {os.getenv('PYTEST_CURRENT_TEST')}")
            print(f"--- {filename} -------")
            print(ast.dump(tree, indent=4))
    code = compile(tree, filename, "exec", dont_inherit=True)
    import contextlib, os
    with open("/tmp/foo.out", "a") as f:
        with contextlib.redirect_stdout(f):
            import dis
            print("----------------------------")
            dis.dis(code)
    return code
