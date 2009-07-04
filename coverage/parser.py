"""Code parsing for Coverage."""

import re, token, tokenize, types
import cStringIO as StringIO

from coverage.misc import nice_pair, CoverageException
from coverage.backward import set   # pylint: disable-msg=W0622
    

class CodeParser:
    """Parse code to find executable lines, excluded lines, etc."""
    
    def __init__(self, show_tokens=False):
        self.show_tokens = show_tokens

        # The text lines of the parsed code.
        self.lines = None

        # The line numbers of excluded lines of code.
        self.excluded = set()
        
        # The line numbers of docstring lines.
        self.docstrings = set()
        
        # A dict mapping line numbers to (lo,hi) for multi-line statements.
        self.multiline = {}
        
        # The line numbers that start statements.
        self.statement_starts = set()

    def find_statement_starts(self, code):
        """Find the starts of statements in compiled code.
    
        Uses co_lnotab described in Python/compile.c to find line numbers that
        start statements, adding them to `self.statement_starts`.
    
        """
        # Adapted from dis.py in the standard library.
        byte_increments = [ord(c) for c in code.co_lnotab[0::2]]
        line_increments = [ord(c) for c in code.co_lnotab[1::2]]
    
        last_line_num = None
        line_num = code.co_firstlineno
        for byte_incr, line_incr in zip(byte_increments, line_increments):
            if byte_incr:
                if line_num != last_line_num:
                    self.statement_starts.add(line_num)
                    last_line_num = line_num
            line_num += line_incr
        if line_num != last_line_num:
            self.statement_starts.add(line_num)

    def find_statements(self, code):
        """Find the statements in `code`.
        
        Update `self.statement_starts`, a set of line numbers that start
        statements.  Recurses into all code objects reachable from `code`.
        
        """
        # Adapted from trace.py in the standard library.

        # Get all of the lineno information from this code.
        self.find_statement_starts(code)
    
        # Check the constants for references to other code objects.
        for c in code.co_consts:
            if isinstance(c, types.CodeType):
                # Found another code object, so recurse into it.
                self.find_statements(c)

    def raw_parse(self, text=None, filename=None, exclude=None):
        """Parse `text` to find the interesting facts about its lines.
        
        A handful of member fields are updated.
        
        """
        if not text:
            sourcef = open(filename, 'rU')
            text = sourcef.read()
            sourcef.close()
        text = text.replace('\r\n', '\n')
        self.lines = text.split('\n')

        # Find lines which match an exclusion pattern.
        if exclude:
            re_exclude = re.compile(exclude)
            for i, ltext in enumerate(self.lines):
                if re_exclude.search(ltext):
                    self.excluded.add(i+1)
    
        # Tokenize, to find excluded suites, to find docstrings, and to find
        # multi-line statements.
        indent = 0
        exclude_indent = 0
        excluding = False
        prev_toktype = token.INDENT
        first_line = None

        tokgen = tokenize.generate_tokens(StringIO.StringIO(text).readline)
        for toktype, ttext, (slineno, _), (elineno, _), ltext in tokgen:
            if self.show_tokens:
                print "%10s %5s %-20r %r" % (
                    tokenize.tok_name.get(toktype, toktype),
                    nice_pair((slineno, elineno)), ttext, ltext
                    )
            if toktype == token.INDENT:
                indent += 1
            elif toktype == token.DEDENT:
                indent -= 1
            elif toktype == token.OP and ttext == ':':
                if not excluding and elineno in self.excluded:
                    # Start excluding a suite.  We trigger off of the colon
                    # token so that the #pragma comment will be recognized on
                    # the same line as the colon.
                    exclude_indent = indent
                    excluding = True
            elif toktype == token.STRING and prev_toktype == token.INDENT:
                # Strings that are first on an indented line are docstrings.
                # (a trick from trace.py in the stdlib.)
                for i in xrange(slineno, elineno+1):
                    self.docstrings.add(i)
            elif toktype == token.NEWLINE:
                if first_line is not None and elineno != first_line:
                    # We're at the end of a line, and we've ended on a
                    # different line than the first line of the statement,
                    # so record a multi-line range.
                    rng = (first_line, elineno)
                    for l in xrange(first_line, elineno+1):
                        self.multiline[l] = rng
                first_line = None
                
            if ttext.strip() and toktype != tokenize.COMMENT:
                # A non-whitespace token.
                if first_line is None:
                    # The token is not whitespace, and is the first in a
                    # statement.
                    first_line = slineno
                    # Check whether to end an excluded suite.
                    if excluding and indent <= exclude_indent:
                        excluding = False
                    if excluding:
                        self.excluded.add(elineno)
                        
            prev_toktype = toktype

        # Find the starts of the executable statements.
        filename = filename or "<code>"
        try:
            # Python 2.3 and 2.4 don't like partial last lines, so be sure the
            # text ends nicely for them.
            text += '\n'
            code = compile(text, filename, "exec")
        except SyntaxError, synerr:
            raise CoverageException(
                "Couldn't parse '%s' as Python source: '%s' at line %d" %
                    (filename, synerr.msg, synerr.lineno)
                )

        self.find_statements(code)

    def map_to_first_line(self, lines, ignore=None):
        """Map the line numbers in `lines` to the correct first line of the
        statement.
        
        Skip any line mentioned in `ignore`.
        
        Returns a sorted list of the first lines.
        
        """
        ignore = ignore or []
        lset = set()
        for l in lines:
            if l in ignore:
                continue
            rng = self.multiline.get(l)
            if rng:
                new_l = rng[0]
            else:
                new_l = l
            if new_l not in ignore:
                lset.add(new_l)
        lines = list(lset)
        lines.sort()
        return lines
    
    def parse_source(self, text=None, filename=None, exclude=None):
        """Parse source text to find executable lines, excluded lines, etc.
        
        Source can be provided as `text`, the text itself, or `filename`, from
        which text will be read.  Excluded lines are those that match `exclude`,
        a regex.
        
        Return values are 1) a sorted list of executable line numbers,
        2) a sorted list of excluded line numbers, and 3) a dict mapping line
        numbers to pairs (lo,hi) for multi-line statements.
        
        """
        self.raw_parse(text, filename, exclude)
        
        excluded_lines = self.map_to_first_line(self.excluded)
        ignore = excluded_lines + list(self.docstrings)
        lines = self.map_to_first_line(self.statement_starts, ignore)
    
        return lines, excluded_lines, self.multiline

    def print_parse_results(self):
        """Print the results of the parsing."""
        for i, ltext in enumerate(self.lines):
            lineno = i+1
            m0 = m1 = m2 = ' '
            if lineno in self.statement_starts:
                m0 = '-'
            if lineno in self.docstrings:
                m1 = '"'
            if lineno in self.excluded:
                m2 = 'x'
            print "%4d %s%s%s %s" % (lineno, m0, m1, m2, ltext)


if __name__ == '__main__':
    import sys
    
    parser = CodeParser(show_tokens=True)
    parser.raw_parse(filename=sys.argv[1], exclude=r"no\s*cover")
    parser.print_parse_results()
