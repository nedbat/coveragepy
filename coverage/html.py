"""HTML reporting for Coverage."""

import os, re, shutil
from coverage import __version__    # pylint: disable-msg=W0611
from coverage.report import Reporter
from coverage.templite import Templite


def data_filename(fname):
    """Return the path to a data file of ours."""
    return os.path.join(os.path.split(__file__)[0], fname)

def data(fname):
    """Return the contents of a data file of ours."""
    return open(data_filename(fname)).read()
    

class HtmlReporter(Reporter):
    """HTML reporting.
    
    """
    
    def __init__(self, coverage, ignore_errors=False):
        super(HtmlReporter, self).__init__(coverage, ignore_errors)
        self.directory = None
        self.source_tmpl = Templite(data("htmlfiles/pyfile.html"), globals())
        
        self.files = []

    def report(self, morfs, directory=None, omit_prefixes=None):
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

    def html_file(self, cu, statements, excluded, missing):
        """Generate an HTML file for one source file."""
        
        source = cu.source_file()
        source_lines = source.readlines()
        
        n_lin = len(source_lines)
        n_stm = len(statements)
        n_exc = len(excluded)
        n_mis = len(missing)
        n_run = n_stm - n_mis
        if n_stm > 0:
            pc_cov = 100.0 * n_run / n_stm
        else:
            pc_cov = 100.0

        # These classes determine which lines are highlighted by default.
        c_run = " run hide"
        c_exc = " exc"
        c_mis = " mis"
        
        lines = []
        for lineno, line in enumerate(source_lines):
            lineno += 1     # enum is 0-based, lines are 1-based.
            
            
            css_class = ""
            if lineno in statements:
                css_class += " stm"
                if lineno not in missing and lineno not in excluded:
                    css_class += c_run
            if lineno in excluded:
                css_class += c_exc
            if lineno in missing:
                css_class += c_mis
                
            lineinfo = {
                'text': line,
                'number': lineno,
                'class': css_class.strip() or "pln"
            }
            lines.append(lineinfo)

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


# Helpers for templates

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

def not_empty(t):
    """Make sure HTML content is not completely empty."""
    return t or "&nbsp;"
    
def format_pct(p):
    return "%.0f" % p

def spaceless(html):
    """Squeeze out some of that annoying extra space that comes from
    nicely-formatted templates."""
    html = re.sub(">\s+<p ", ">\n<p ", html)
    return html
