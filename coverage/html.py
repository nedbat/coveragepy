"""HTML reporting for Coverage."""

import os, re, shutil

from coverage import __url__, __version__           # pylint: disable-msg=W0611
from coverage.phystokens import source_token_lines
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
    

class HtmlReporter(Reporter):
    """HTML reporting."""
    
    def __init__(self, coverage, ignore_errors=False):
        super(HtmlReporter, self).__init__(coverage, ignore_errors)
        self.directory = None
        self.source_tmpl = Templite(data("htmlfiles/pyfile.html"), globals())
        
        self.files = []
        self.arcs = coverage.data.has_arcs()

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
        for static in [
            "style.css", "coverage_html.js",
            "jquery-1.3.2.min.js", "jquery.tablesorter.min.js"
            ]:
            shutil.copyfile(
                data_filename("htmlfiles/" + static),
                os.path.join(directory, static)
                )

    def html_file(self, cu, analysis):
        """Generate an HTML file for one source file."""
        
        source = cu.source_file().read()

        nums = analysis.numbers        

        missing_branch_arcs = analysis.missing_branch_arcs()
        n_par = 0   # accumulated below.
        arcs = self.arcs

        # These classes determine which lines are highlighted by default.
        c_run = " run hide_run"
        c_exc = " exc"
        c_mis = " mis"
        c_par = " par" + c_run

        lines = []
        
        for lineno, line in enumerate(source_token_lines(source)):
            lineno += 1     # 1-based line numbers.
            # Figure out how to mark this line.
            line_class = ""
            annotate = ""
            if lineno in analysis.statements:
                line_class += " stm"
            if lineno in analysis.excluded:
                line_class += c_exc
            elif lineno in analysis.missing:
                line_class += c_mis
            elif self.arcs and lineno in missing_branch_arcs:
                line_class += c_par
                n_par += 1
                annlines = []
                for b in missing_branch_arcs[lineno]:
                    if b == -1:
                        annlines.append("exit")
                    else:
                        annlines.append(str(b))
                annotate = " ".join(annlines)
            elif lineno in analysis.statements:
                line_class += c_run
            
            # Build the HTML for the line
            html = ""
            for tok_type, tok_text in line:
                if tok_type == "ws":
                    html += escape(tok_text)
                else:
                    tok_html = escape(tok_text) or '&nbsp;'
                    html += "<span class='%s'>%s</span>" % (tok_type, tok_html)

            lines.append({
                'html': html,
                'number': lineno,
                'class': line_class.strip() or "pln",
                'annotate': annotate,
            })

        # Write the HTML page for this file.
        html_filename = cu.flat_rootname() + ".html"
        html_path = os.path.join(self.directory, html_filename)
        html = spaceless(self.source_tmpl.render(locals()))
        fhtml = open(html_path, 'w')
        fhtml.write(html)
        fhtml.close()

        # Save this file's information for the index file.
        self.files.append({
            'nums': nums,
            'par': n_par,
            'html_filename': html_filename,
            'cu': cu,
            })

    def index_file(self):
        """Write the index.html file for this report."""
        index_tmpl = Templite(data("htmlfiles/index.html"), globals())

        files = self.files
        arcs = self.arcs

        totals = sum([f['nums'] for f in files])

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
            # Convert runs of spaces: "......" -> "&nbsp;.&nbsp;.&nbsp;."
            .replace("  ", "&nbsp; ")
            # To deal with odd-length runs, convert the final pair of spaces
            # so that "....." -> "&nbsp;.&nbsp;&nbsp;."
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
