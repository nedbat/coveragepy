"""Results of coverage measurement."""

import os

from coverage.backward import set, sorted           # pylint: disable-msg=W0622
from coverage.misc import format_lines, NoSource
from coverage.parser import CodeParser


class Analysis(object):
    """The results of analyzing a code unit."""
    
    def __init__(self, cov, code_unit):
        self.coverage = cov
        self.code_unit = code_unit
        
        self.filename = self.code_unit.filename
        ext = os.path.splitext(self.filename)[1]
        source = None
        if ext == '.py':
            if not os.path.exists(self.filename):
                source = self.coverage.file_locator.get_zip_data(self.filename)
                if not source:
                    raise NoSource("No source for code: %r" % self.filename)

        self.parser = CodeParser(
            text=source, filename=self.filename,
            exclude=self.coverage.exclude_re
            )
        self.statements, self.excluded = self.parser.parse_source()

        # Identify missing statements.
        executed = self.coverage.data.executed_lines(self.filename)
        exec1 = [l for l in self.parser.first_lines(executed) if l in self.statements]
        exec1 = self.parser.first_lines(executed)
        self.missing = sorted(set(self.statements) - set(exec1))

        if self.coverage.data.has_arcs():
            n_branches = self.total_branches()
            mba = self.missing_branch_arcs()
            n_missing_branches = sum([len(v) for v in mba.values()])
        else:
            n_branches = n_missing_branches = 0
            
        self.numbers = Numbers(
            n_files=1,
            n_statements=len(self.statements), 
            n_excluded=len(self.excluded),
            n_missing=len(self.missing),
            n_branches=n_branches,
            n_missing_branches=n_missing_branches,
            )

    def missing_formatted(self):
        """The missing line numbers, formatted nicely.
        
        Returns a string like "1-2, 5-11, 13-14".
        
        """
        return format_lines(self.statements, self.missing)

    def has_arcs(self):
        """Were arcs measured in this result?"""
        return self.coverage.data.has_arcs()

    def arc_possibilities(self):
        """Returns a sorted list of the arcs in the code."""
        return self.parser.arcs()

    def arcs_executed(self):
        """Returns a sorted list of the arcs actually executed in the code."""
        executed = self.coverage.data.executed_arcs(self.filename)
        m2fl = self.parser.first_line
        executed = [(m2fl(l1), m2fl(l2)) for (l1,l2) in executed]
        return sorted(executed)

    def arcs_missing(self):
        """Returns a sorted list of the arcs in the code not executed."""
        possible = self.arc_possibilities()
        executed = self.arcs_executed()
        missing = [p for p in possible if p not in executed]
        return sorted(missing)

    def arcs_unpredicted(self):
        """Returns a sorted list of the executed arcs missing from the code."""
        possible = self.arc_possibilities()
        executed = self.arcs_executed()
        # Exclude arcs here which connect a line to itself.  They can occur
        # in executed data in some cases.  This is where they can cause
        # trouble, and here is where it's the least burden to remove them.
        unpredicted = [
            e for e in executed
                if e not in possible and e[0] != e[1]
            ]
        return sorted(unpredicted)

    def branch_lines(self):
        """Returns lines that have more than one exit."""
        exit_counts = {}
        for l1,l2 in self.arc_possibilities():
            if l1 == -1:
                continue
            if l1 not in exit_counts:
                exit_counts[l1] = 0
            exit_counts[l1] += 1
        
        return [l1 for l1,count in exit_counts.items() if count > 1]

    def total_branches(self):
        exit_counts = {}
        for l1,l2 in self.arc_possibilities():
            if l1 == -1:
                continue
            if l1 not in exit_counts:
                exit_counts[l1] = 0
            exit_counts[l1] += 1
        
        return sum([count for count in exit_counts.values() if count > 1])
        
    def missing_branch_arcs(self):
        """Return arcs that weren't executed from branch lines.
        
        Returns {l1:[l2a,l2b,...], ...}
        
        """
        missing = self.arcs_missing()
        branch_lines = set(self.branch_lines())
        mba = {}
        for l1, l2 in missing:
            if l1 in branch_lines:
                if l1 not in mba:
                    mba[l1] = []
                mba[l1].append(l2)
        return mba


class Numbers(object):
    """The numerical results of measuring coverage.
    
    This holds the basic statistics from `Analysis`, and is used to roll
    up statistics across files.

    """
    def __init__(self, n_files=0, n_statements=0, n_excluded=0, n_missing=0,
                    n_branches=0, n_missing_branches=0
                    ):
        self.n_files = n_files
        self.n_statements = n_statements
        self.n_excluded = n_excluded
        self.n_missing = n_missing
        self.n_branches = n_branches
        self.n_missing_branches = n_missing_branches

    def _get_n_executed(self):
        """Returns the number of executed statements."""
        return self.n_statements - self.n_missing
    n_executed = property(_get_n_executed)
    
    def _get_n_executed_branches(self):
        """Returns the number of executed branches."""
        return self.n_branches - self.n_missing_branches
    n_executed_branches = property(_get_n_executed_branches)
    
    def _get_pc_covered(self):
        """Returns a single percentage value for coverage."""
        if self.n_statements > 0:
            pc_cov = 100.0 * (self.n_executed + self.n_executed_branches) / (self.n_statements + self.n_branches)
        else:
            pc_cov = 100.0
        return pc_cov
    pc_covered = property(_get_pc_covered)

    def __add__(self, other):
        nums = Numbers()
        nums.n_files = self.n_files + other.n_files
        nums.n_statements = self.n_statements + other.n_statements
        nums.n_excluded = self.n_excluded + other.n_excluded
        nums.n_missing = self.n_missing + other.n_missing
        nums.n_branches = self.n_branches + other.n_branches
        nums.n_missing_branches = self.n_missing_branches + other.n_missing_branches
        return nums

    def __radd__(self, other):
        # Implementing 0+Numbers allows us to sum() a list of Numbers.
        if other == 0:
            return self
        raise NotImplemented
