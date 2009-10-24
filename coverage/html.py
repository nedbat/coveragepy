"""HTML reporting for Coverage."""

import keyword, os, re, token, tokenize, shutil
from coverage import __url__, __version__    # pylint: disable-msg=W0611
from coverage.backward import StringIO   # pylint: disable-msg=W0622
from coverage.report import Reporter
from coverage.templite import Templite

# Disable pylint msg W0612, because a bunch of variables look unused, but
# they're accessed in a templite context via locals().
# pylint: disable-msg=W0612

def data_filename(fname):
    """Return the path to a data file of ours."""
    return os.path.join(os.path.split(__file__)[0], fname)

def data(fname):
    """Return the contents of a data file of ours."""
    return open(data_filename(fname)).read()
    

def phys_tokens(toks):
    """Return all physical tokens, even line continuations.
    
    tokenize.generate_tokens() doesn't return a token for the backslash that
    continues lines.  This wrapper provides those tokens so that we can
    re-create a faithful representation of the original source.
    
    Returns the same values as generate_tokens()
    
    """
    last_line = None
    last_lineno = -1
    for ttype, ttext, (slineno, scol), (elineno, ecol), ltext in toks:
        if last_lineno != elineno:
            if last_line and last_line[-2:] == "\\\n":
                if ttype != token.STRING:
                    ccol = len(last_line.split("\n")[-2]) - 1
                    yield (
                        99999, "\\\n",
                        (slineno, ccol), (slineno, ccol+2),
                        last_line
                        )
            last_line = ltext
        yield ttype, ttext, (slineno, scol), (elineno, ecol), ltext
        last_lineno = elineno


class HtmlReporter(Reporter):
    """HTML reporting."""
    
    def __init__(self, coverage, ignore_errors=False):
        super(HtmlReporter, self).__init__(coverage, ignore_errors)
        self.directory = None
        self.source_tmpl = Templite(data("htmlfiles/pyfile.html"), globals())
        
        self.files = []

    def report(self, morfs, directory, omit_prefixes=None):
        """Generate an HTML report for `morfs`.
        
        `morfs` is a list of modules or filenames.  `directory` is where to put
        the HTML files. `omit_prefixes` is a list of strings, prefixes of
        modules to omit from the report.
        
        """
        assert directory, "must provide a directory for html reporting"
        
        # Process all the files.
        self.report_files(self.html_file, morfs, directory, omit_prefixes)

        # Write the index file.
        self.index_file()

        # Create the once-per-directory files.
        shutil.copyfile(
            data_filename("htmlfiles/style.css"),
            os.path.join(directory, "style.css")
            )
        shutil.copyfile(
            data_filename("htmlfiles/jquery-1.3.2.min.js"),
            os.path.join(directory, "jquery-1.3.2.min.js")
            )

    def html_file(self, cu, analysis):
        """Generate an HTML file for one source file."""
        
        source = cu.source_file().read().expandtabs(4)
        source_lines = source.split("\n")
        
        n_stm = len(analysis.statements)
        n_exc = len(analysis.excluded)
        n_mis = len(analysis.missing)
        n_run = n_stm - n_mis
        if n_stm > 0:
            pc_cov = 100.0 * n_run / n_stm
        else:
            pc_cov = 100.0

        # These classes determine which lines are highlighted by default.
        c_run = " run hide"
        c_exc = " exc"
        c_mis = " mis"
        
        ws_tokens = [token.INDENT, token.DEDENT, token.NEWLINE, tokenize.NL]
        lines = []
        line = []
        lineno = 1
        col = 0
        tokgen = tokenize.generate_tokens(StringIO(source).readline)
        for ttype, ttext, (_, scol), (_, ecol), _ in phys_tokens(tokgen):
            mark_start = True
            for part in re.split('(\n)', ttext):
                if part == '\n':

                    line_class = ""
                    if lineno in analysis.statements:
                        line_class += " stm"
                        if lineno not in analysis.missing and \
                            lineno not in analysis.excluded:
                            line_class += c_run
                    if lineno in analysis.excluded:
                        line_class += c_exc
                    if lineno in analysis.missing:
                        line_class += c_mis
                        
                    lineinfo = {
                        'html': "".join(line),
                        'number': lineno,
                        'class': line_class.strip() or "pln"
                    }
                    lines.append(lineinfo)
                    
                    line = []
                    lineno += 1
                    col = 0
                    mark_end = False
                elif part == '':
                    mark_end = False
                elif ttype in ws_tokens:
                    mark_end = False
                else:
                    if mark_start and scol > col:
                        line.append(escape(" " * (scol - col)))
                        mark_start = False
                    tok_class = tokenize.tok_name.get(ttype, 'xx').lower()[:3]
                    if ttype == token.NAME and keyword.iskeyword(ttext):
                        tok_class = "key"
                    tok_html = escape(part) or '&nbsp;'
                    line.append(
                        "<span class='%s'>%s</span>" % (tok_class, tok_html)
                        )
                    mark_end = True
                scol = 0
            if mark_end:
                col = ecol

        # Write the HTML page for this file.
        html_filename = cu.flat_rootname() + ".html"
        html_path = os.path.join(self.directory, html_filename)
        html = spaceless(self.source_tmpl.render(locals()))
        fhtml = open(html_path, 'w')
        fhtml.write(html)
        fhtml.close()

        # Save this file's information for the index file.
        self.files.append({
            'stm': n_stm,
            'run': n_run,
            'exc': n_exc,
            'mis': n_mis,
            'pc_cov': pc_cov,
            'html_filename': html_filename,
            'cu': cu,
            })

    def index_file(self):
        """Write the index.html file for this report."""
        index_tmpl = Templite(data("htmlfiles/index.html"), globals())

        files = self.files
        
        total_stm = sum([f['stm'] for f in files])
        total_run = sum([f['run'] for f in files])
        total_exc = sum([f['exc'] for f in files])
        if total_stm:
            total_cov = 100.0 * total_run / total_stm
        else:
            total_cov = 100.0

        fhtml = open(os.path.join(self.directory, "index.html"), "w")
        fhtml.write(index_tmpl.render(locals()))
        fhtml.close()


# Helpers for templates and generating HTML

def escape(t):
    """HTML-escape the text in t."""
    return (t
            # Convert HTML special chars into HTML entities.
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace("'", "&#39;").replace('"', "&quot;")
            # Convert runs of spaces: "      " -> "&nbsp; &nbsp; &nbsp; "
            .replace("  ", "&nbsp; ")
            # To deal with odd-length runs, convert the final pair of spaces
            # so that "     " -> "&nbsp; &nbsp;&nbsp; "
            .replace("  ", "&nbsp; ")
        )

def format_pct(p):
    """Format a percentage value for the HTML reports."""
    return "%.0f" % p

def spaceless(html):
    """Squeeze out some annoying extra space from an HTML string.
    
    Nicely-formatted templates mean lots of extra space in the result.  Get
    rid of some.
    
    """
    html = re.sub(">\s+<p ", ">\n<p ", html)
    return html
