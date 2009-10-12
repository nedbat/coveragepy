"""Code parsing for Coverage."""

import glob, opcode, os, re, sys, token, tokenize

from coverage.backward import set, StringIO   # pylint: disable-msg=W0622
from coverage.bytecode import ByteCodes, CodeObjects
from coverage.misc import nice_pair, CoverageException


class CodeParser:
    """Parse code to find executable lines, excluded lines, etc."""
    
    def __init__(self):
        self.show_tokens = False

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

    # Getting numbers from the lnotab value changed in Py3.0.    
    if sys.hexversion >= 0x03000000:
        def _lnotab_increments(self, lnotab):
            """Return a list of ints from the lnotab bytes in 3.x"""
            return list(lnotab)
    else:
        def _lnotab_increments(self, lnotab):
            """Return a list of ints from the lnotab string in 2.x"""
            return [ord(c) for c in lnotab]

    def _bytes_lines(self, code):
        """Map byte offsets to line numbers in `code`.
    
        Uses co_lnotab described in Python/compile.c to map byte offsets to
        line numbers.  Returns a list: [(b0, l0), (b1, l1), ...]
    
        """
        # Adapted from dis.py in the standard library.
        byte_increments = self._lnotab_increments(code.co_lnotab[0::2])
        line_increments = self._lnotab_increments(code.co_lnotab[1::2])
    
        bytes_lines = []
        last_line_num = None
        line_num = code.co_firstlineno
        byte_num = 0
        for byte_incr, line_incr in zip(byte_increments, line_increments):
            if byte_incr:
                if line_num != last_line_num:
                    bytes_lines.append((byte_num, line_num))
                    last_line_num = line_num
                byte_num += byte_incr
            line_num += line_incr
        if line_num != last_line_num:
            bytes_lines.append((byte_num, line_num))
        return bytes_lines
    
    def _find_statements(self, code):
        """Find the statements in `code`.
        
        Update `self.statement_starts`, a set of line numbers that start
        statements.  Recurses into all code objects reachable from `code`.
        
        """
        # Adapted from trace.py in the standard library.
        for co in CodeObjects(code):
            # Get all of the lineno information from this code.
            bytes_lines = self._bytes_lines(co)
            for b, l in bytes_lines:
                self.statement_starts.add(l)
    
    def _raw_parse(self, text=None, filename=None, exclude=None):
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

        tokgen = tokenize.generate_tokens(StringIO(text).readline)
        for toktype, ttext, (slineno, _), (elineno, _), ltext in tokgen:
            if self.show_tokens:
                print("%10s %5s %-20r %r" % (
                    tokenize.tok_name.get(toktype, toktype),
                    nice_pair((slineno, elineno)), ttext, ltext
                    ))
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
                for i in range(slineno, elineno+1):
                    self.docstrings.add(i)
            elif toktype == token.NEWLINE:
                if first_line is not None and elineno != first_line:
                    # We're at the end of a line, and we've ended on a
                    # different line than the first line of the statement,
                    # so record a multi-line range.
                    rng = (first_line, elineno)
                    for l in range(first_line, elineno+1):
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
        except SyntaxError:
            _, synerr, _ = sys.exc_info()
            raise CoverageException(
                "Couldn't parse '%s' as Python source: '%s' at line %d" %
                    (filename, synerr.msg, synerr.lineno)
                )

        self._find_statements(code)

    def _map_to_first_line(self, lines, ignore=None):
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
        self._raw_parse(text, filename, exclude)
        
        excluded_lines = self._map_to_first_line(self.excluded)
        ignore = excluded_lines + list(self.docstrings)
        lines = self._map_to_first_line(self.statement_starts, ignore)
    
        return lines, excluded_lines, self.multiline

    def _disassemble(self, code):
        """Disassemble code, for ad-hoc experimenting."""
        
        import dis
        
        for codeobj in CodeObjects(code):
            print("\n%s: " % codeobj)
            dis.dis(codeobj)
            print("Bytes lines: %r" % self._bytes_lines(codeobj))
            print("Jumps: %r %r" % self._find_byte_jumps(codeobj))
            warnings, chunks = self._split_into_chunks(codeobj)
            if warnings:
                print("WARNING: %s" % "\n".join(warnings))

        print("")

    def _line_for_byte(self, bytes_lines, byte):
        last_line = 0
        for b, l in bytes_lines:
            if b == byte:
                return l
            elif b > byte:
                return last_line
            else:
                last_line = l
        return last_line

    def _find_byte_jumps(self, code):
        byte_jumps = [(bc.offset, bc.jump_to) for bc in ByteCodes(code.co_code) if bc.jump_to >= 0]
        
        bytes_lines = self._bytes_lines(code)
        line_jumps = [(self._line_for_byte(bytes_lines, b0), self._line_for_byte(bytes_lines, b1)) for b0, b1 in byte_jumps]
        return byte_jumps, line_jumps

    _chunk_enders = set([opcode.opmap[name] for name in ['JUMP_ABSOLUTE', 'JUMP_FORWARD', 'RETURN_VALUE']])
    
    def _split_into_chunks(self, code):
        class Chunk(object):
            def __init__(self, byte, line=0):
                self.byte = byte
                self.line = line
                self.exits = set()
                
            def __repr__(self):
                return "<%d:%d %r>" % (self.byte, self.line, list(self.exits))

        chunks = []
        chunk = None
        bytes_lines_map = dict(self._bytes_lines(code))
        
        for bc in ByteCodes(code.co_code):
            # Maybe have to start a new block
            if bc.offset in bytes_lines_map:
                if chunk:
                    chunk.exits.add(bc.offset)
                chunk = Chunk(bc.offset, bytes_lines_map[bc.offset])
                chunks.append(chunk)
                
            if not chunk:
                chunk = Chunk(bc.offset)
                chunks.append(chunk)
                
            if bc.jump_to >= 0:
                chunk.exits.add(bc.jump_to)
            
            if bc.op in self._chunk_enders:
                chunk = None
        
        warnings = []
        # Find anonymous chunks (not associated with a line number), and find
        # the numbered chunks that jump to them.
        for ch in chunks:
            if not ch.line:
                jumpers = [c for c in chunks if ch.byte in c.exits]
                if len(jumpers) == 1:
                    ch.line = jumpers[0].line
                if len(jumpers) > 1:
                    warnings.append("Anon chunk at %d has %d jumpers" % (ch.byte, len(jumpers)))
                #if len(ch.exits) > 1:
                #    warnings.append("Anon chunk at %d has %d exits" % (ch.byte, len(ch.exits)))
        return warnings, chunks

    def _all_chunks(self, code):
        warnings = []
        chunks = []
        for co in CodeObjects(code):
            warns, chs = self._split_into_chunks(co)
            warnings.extend(warns)
            chunks.extend(chs)
        
        return warnings, chunks
            
    def adhoc_main(self, args):
        """A main function for trying the code from the command line."""

        from optparse import OptionParser

        parser = OptionParser()
        parser.add_option(
            "-c", action="store_true", dest="chunks", help="Check byte chunks"
            )
        parser.add_option(
            "-d", action="store_true", dest="dis", help="Disassemble"
            )
        parser.add_option(
            "-R", action="store_true", dest="recursive", help="Recurse to find source files"
            )
        parser.add_option(
            "-s", action="store_true", dest="source", help="Show analyzed source"
            )
        parser.add_option(
            "-t", action="store_true", dest="tokens", help="Show tokens"
            )
        
        options, args = parser.parse_args()
        if options.recursive:
            if args:
                root = args[0]
            else:
                root = "."
            for root, _, _ in os.walk(root):
                for f in glob.glob(root + "/*.py"):
                    self.adhoc_one_file(options, f)
        else:
            self.adhoc_one_file(options, args[0])

    def adhoc_one_file(self, options, filename):
        if options.dis or options.chunks:        
            source = open(filename, "rU").read() + "\n\n"
            try:
                code = compile(source, filename, "exec")
            except SyntaxError:
                _, err, _ = sys.exc_info()                
                print("** Couldn't compile %s: %s" % (filename, err))
                return

        if options.dis:
            print("Main code:")
            self._disassemble(code)

        if options.chunks:
            warnings, chunks = self._all_chunks(code)
            if options.recursive:
                print("%6d: %s" % (len(chunks), filename))
                if warnings:
                    print("\t%r" % (warnings,))
            else:
                print(warnings)
                print(chunks)

        self.show_tokens = options.tokens
        self._raw_parse(filename=filename, exclude=r"no\s*cover")

        if options.source:
            for i, ltext in enumerate(self.lines):
                lineno = i+1
                m0 = m1 = m2 = ' '
                if lineno in self.statement_starts:
                    m0 = '-'
                if lineno in self.docstrings:
                    m1 = '"'
                if lineno in self.excluded:
                    m2 = 'x'
                print("%4d %s%s%s %s" % (lineno, m0, m1, m2, ltext))


if __name__ == '__main__':
    CodeParser().adhoc_main(sys.argv[1:])
