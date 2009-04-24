"""HTML reporting for coverage.py"""

import os, shutil
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
        
    def report(self, morfs, directory=None, omit_prefixes=None):
        assert directory, "must provide a directory for html reporting"
        # Create the once-per-directory files.
        shutil.copyfile(
            data_filename("htmlfiles/style.css"),
            os.path.join(directory, "style.css")
            )

        # Process all the files.
        self.report_files(self.html_file, morfs, directory, omit_prefixes)

    def html_file(self, cu, statements, excluded, missing):
        """Generate an HTML file for one source file."""
        
        source = cu.source_file()
        source_lines = source.readlines()
        
        n_lin = len(source_lines)
        n_stm = len(statements)
        n_exc = len(excluded)
        n_mis = len(missing)
        if n_stm > 0:
            pc_cov = 100.0 * float(n_mis) / n_stm
        else:
            pc_cov = 100.0

        lines = []
        for lineno, line in enumerate(source_lines):
            lineno += 1     # enum is 0-based, lines are 1-based.
            
            
            css_class = ""
            if lineno in statements:
                css_class += " stm"
                if lineno not in missing and lineno not in excluded:
                    css_class += " run"
            if lineno in excluded:
                css_class += " exc"
            if lineno in missing:
                css_class += " mis"
                
            lineinfo = {
                'text': line,
                'number': lineno,
                'class': css_class.strip() or "pln"
            }
            lines.append(lineinfo)

        html_filename = os.path.join(self.directory, cu.flat_rootname())
        html_filename += ".html"
        fhtml = open(html_filename, 'w')
        fhtml.write(self.source_tmpl.render(locals()))
        fhtml.close()


# Helpers for templates

def escape(t):
    """HTML-escape the text in t."""
    return (t
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace("'", "&#39;").replace('"', "&quot;")
            .replace("  ", "&nbsp; ")
        )

def not_empty(t):
    """Make sure HTML content is not completely empty."""
    return t or "&nbsp;"
    
def format_pct(p):
    return "%.0f" % p
