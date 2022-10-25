# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Summary reporting"""

import sys

from coverage.exceptions import ConfigError, NoDataError
from coverage.misc import human_key
from coverage.report import get_analysis_to_report
from coverage.results import Numbers


class SummaryReporter:
    """A reporter for writing the summary report."""

    def __init__(self, coverage):
        self.coverage = coverage
        self.config = self.coverage.config
        self.branches = coverage.get_data().has_arcs()
        self.outfile = None
        self.fr_analysis = []
        self.skipped_count = 0
        self.empty_count = 0
        self.total = Numbers(precision=self.config.precision)
        self.fmt_err = "%s   %s: %s"

    def writeout(self, line):
        """Write a line to the output, adding a newline."""
        self.outfile.write(line.rstrip())
        self.outfile.write("\n")

    def _report_text(self, header, lines_values, total_line, end_lines):
        "internal method to print report data in text format"
        # Prepare the formatting strings, header, and column sorting.
        max_name = max([len(fr.relative_filename()) for (fr, analysis) in \
            self.fr_analysis] + [5]) + 2
        n = self.config.precision
        max_n = max(n+6, 7)
        h_form = dict(
            Name="{:{name_len}}", Stmts="{:>7}", Miss="{:>7}",
            Branch="{:>7}", BrPart="{:>7}", Cover="{:>{n}}",
            Missing="{:>9}")
        header_items = [
            h_form[item].format(item, name_len=max_name, n=max_n)
            for item in header]
        header_str = "".join(header_items)
        rule = "-" * len(header_str)

        # Write the header
        self.writeout(header_str)
        self.writeout(rule)

        column_order = dict(name=0, stmts=1, miss=2, cover=-1)
        if self.branches:
            column_order.update(dict(branch=3, brpart=4))

        h_form.update(dict(Cover="{:>{n}}%"), Missing=" {:9}")
        for values in lines_values:
            # build string with line values
            line_items = [
                h_form[item].format(str(value),
                name_len=max_name, n=max_n-1) for item, value in zip(header, values)]
            text = "".join(line_items)
            self.writeout(text)

        # Write a TOTAL line
        if total_line:
            self.writeout(rule)
            line_items = [
                h_form[item].format(str(value),
                name_len=max_name, n=max_n-1) for item, value in zip(header, total_line)]
            text = "".join(line_items)
            self.writeout(text)

        for end_line in end_lines:
            self.writeout(end_line)
        return self.total.n_statements and self.total.pc_covered

    def _report_markdown(self, header, lines_values, total_line, end_lines):
        "internal method to print report data in markdown format"
        # Prepare the formatting strings, header, and column sorting.
        max_name = max([len(fr.relative_filename().replace("_","\\_")) for\
            (fr, analysis) in self.fr_analysis] + [9]) + 1
        h_form = dict(
            Name="| {:{name_len}}|", Stmts="{:>7} |", Miss="{:>7} |",
            Branch="{:>7} |", BrPart="{:>7} |", Cover="{:>{n}} |",
            Missing="{:>9} |")
        n = self.config.precision
        max_n = max(n+6, 7) + 4
        header_items = [
            h_form[item].format(item, name_len=max_name, n=max_n) for item in header]
        header_str = "".join(header_items)
        rule_str = "|" + " ".join(["- |".rjust(len(header_items[0])-1, '-')] +
            ["-: |".rjust(len(item)-1, '-') for item in header_items[1:]])

        # Write the header
        self.writeout(header_str)
        self.writeout(rule_str)

        column_order = dict(name=0, stmts=1, miss=2, cover=-1)
        if self.branches:
            column_order.update(dict(branch=3, brpart=4))

        for values in lines_values:
            # build string with line values
            h_form.update(dict(Cover="{:>{n}}% |"))
            line_items = [
                h_form[item].format(str(value).replace("_", "\\_"),
                name_len=max_name, n=max_n-1) for item, value in zip(header, values)]
            text = "".join(line_items)
            self.writeout(text)

        # Write the TOTAL line
        if total_line:
            total_form = dict(
                Name="| {:>{name_len}}** |", Stmts="{:>5}** |", Miss="{:>5}** |",
                Branch="{:>5}** |", BrPart="{:>5}** |", Cover="{:>{n}}%** |",
                Missing="{:>9} |")
            total_line_items = []
            for item, value in zip(header, total_line):
                if item == "Missing":
                    if value == '':
                        insert = value
                    else:
                        insert = "**" + value + "**"
                    total_line_items += total_form[item].format(\
                        insert, name_len=max_name-3)
                else:
                    total_line_items += total_form[item].format(\
                        "**"+str(value), name_len=max_name-3, n=max_n-3)
            total_row_str = "".join(total_line_items)
            self.writeout(total_row_str)
        for end_line in end_lines:
            self.writeout(end_line)
        return self.total.n_statements and self.total.pc_covered


    def report(self, morfs, outfile=None):
        """Writes a report summarizing coverage statistics per module.

        `outfile` is a file object to write the summary to. It must be opened
        for native strings (bytes on Python 2, Unicode on Python 3).

        """
        self.outfile = outfile or sys.stdout

        self.coverage.get_data().set_query_contexts(self.config.report_contexts)
        for fr, analysis in get_analysis_to_report(self.coverage, morfs):
            self.report_one_file(fr, analysis)

        # Prepare the formatting strings, header, and column sorting.
        header = ("Name", "Stmts", "Miss",)
        if self.branches:
            header += ("Branch", "BrPart",)
        header += ("Cover",)
        if self.config.show_missing:
            header += ("Missing",)

        column_order = dict(name=0, stmts=1, miss=2, cover=-1)
        if self.branches:
            column_order.update(dict(branch=3, brpart=4))

        # `lines_values` is list of tuples of sortable values.
        lines_values = []

        for (fr, analysis) in self.fr_analysis:
            nums = analysis.numbers

            args = (fr.relative_filename(), nums.n_statements, nums.n_missing)
            if self.branches:
                args += (nums.n_branches, nums.n_partial_branches)
            args += (nums.pc_covered_str,)
            if self.config.show_missing:
                args += (analysis.missing_formatted(branches=True),)
            args += (nums.pc_covered,)
            lines_values.append(args)

        # line-sorting.
        sort_option = (self.config.sort or "name").lower()
        reverse = False
        if sort_option[0] == '-':
            reverse = True
            sort_option = sort_option[1:]
        elif sort_option[0] == '+':
            sort_option = sort_option[1:]
        sort_idx = column_order.get(sort_option)
        if sort_idx is None:
            raise ConfigError(f"Invalid sorting option: {self.config.sort!r}")
        if sort_option == "name":
            lines_values.sort(key=lambda tup: (human_key(tup[0]), tup[1]),
                reverse=reverse)
        else:
            lines_values.sort(key=lambda tup: (tup[sort_idx], tup[0]),
                reverse=reverse)

        # calculate total if we had at least one file.
        total_line = ()
        if self.total.n_files > 0:
            total_line = ("TOTAL", self.total.n_statements, self.total.n_missing)
            if self.branches:
                total_line += (self.total.n_branches, self.total.n_partial_branches)
            total_line += (self.total.pc_covered_str,)
            if self.config.show_missing:
                total_line += ("",)

        # create other final lines
        end_lines = []
        if not self.total.n_files and not self.skipped_count:
            raise NoDataError("No data to report.")

        if self.config.skip_covered and self.skipped_count:
            file_suffix = 's' if self.skipped_count>1 else ''
            fmt_skip_covered = f"\n{self.skipped_count} file{file_suffix} "\
                "skipped due to complete coverage."
            end_lines.append(fmt_skip_covered)
        if self.config.skip_empty and self.empty_count:
            file_suffix = 's' if self.empty_count>1 else ''
            fmt_skip_empty = \
                f"\n{self.empty_count} empty file{file_suffix} skipped."
            end_lines.append(fmt_skip_empty)

        text_format = self.config.output_format or 'text'
        if text_format.lower() == 'markdown':
            self._report_markdown(header, lines_values, total_line, end_lines)
        else:
            self._report_text(header, lines_values, total_line, end_lines)

        return self.total.n_statements and self.total.pc_covered

    def report_one_file(self, fr, analysis):
        """Report on just one file, the callback from report()."""
        nums = analysis.numbers
        self.total += nums

        no_missing_lines = (nums.n_missing == 0)
        no_missing_branches = (nums.n_partial_branches == 0)
        if self.config.skip_covered and no_missing_lines and no_missing_branches:
            # Don't report on 100% files.
            self.skipped_count += 1
        elif self.config.skip_empty and nums.n_statements == 0:
            # Don't report on empty files.
            self.empty_count += 1
        else:
            self.fr_analysis.append((fr, analysis))
