"""Tests of coverage/debug.py"""

from coverage.debug import info_formatter
from tests.coveragetest import CoverageTest


class InfoFormatterTest(CoverageTest):
    """Tests of misc.info_formatter."""

    def test_info_formatter(self):
        lines = list(info_formatter([
            ('x', 'hello there'),
            ('very long label', ['one element']),
            ('regular', ['abc', 'def', 'ghi', 'jkl']),
            ('nothing', []),
        ]))
        self.assertEqual(lines, [
            '              x: hello there',
            'very long label: one element',
            '        regular: abc',
            '                 def',
            '                 ghi',
            '                 jkl',
            '        nothing: -none-',
        ])
