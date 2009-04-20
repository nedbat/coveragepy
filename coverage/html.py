"""HTML reporting for coverage.py"""

import os
from coverage.report import Reporter
from coverage.templite import Templite

class HtmlReporter(Reporter):
    """HTML reporting.
    
    """
    
    def __init__(self, coverage, ignore_errors=False):
        super(HtmlReporter, self).__init__(coverage, ignore_errors)
        self.directory = None
        self.source_tmpl = Templite(SOURCE, globals())
        
    def report(self, morfs, directory=None, omit_prefixes=None):
        assert directory, "must provide a directory for html reporting"
        self.report_files(self.html_file, morfs, directory, omit_prefixes)

    def html_file(self, cu, statements, excluded, missing):
        """Generate an HTML file for one source file."""
        
        lines = []
        source = cu.source_file()
        for lineno, line in enumerate(source.readlines()):
            lineno += 1
            
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

        html_filename = os.path.join(self.directory, cu.flat_rootname()) + ".html"
        fhtml = open(html_filename, 'w')
        fhtml.write(self.source_tmpl.render(locals()))
        fhtml.close()


# Helpers for templates

def escape(t):
    """HTML-escape the text in t."""
    return (
        t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace("'", "&#39;").replace('"', "&quot;")
            .replace("  ", "&nbsp; ")
        )

def not_empty(t):
    """Make sure HTML content is not completely empty."""
    return t or "&nbsp;"
    

# Templates

SOURCE = """\
<!doctype html PUBLIC "-//W3C//DTD html 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
<title>Coverage of {{cu.filename|escape}}</title>
<style>
.linenos {
    background: #eee;    
    }
.linenos p {
    text-align: right;
    margin: 0;
    padding: 0 .5em 0 .5em;
    font-family: "courier new", monospace;
    color: #999;
    }
.source p {
    margin: 0;
    padding: 0 0 0 .5em;
    font-family: "courier new", monospace;
    white-space: nowrap;  
    }

.linenos p.mis {
    background: #ffcccc;
    }
.linenos p.run {
    background: #ccffcc;
    }
.linenos p.exc {
    background: #e2e2e2;
    }

.source p.mis {
    background: #ffdddd;
    }
.source p.run {
    background: #ddffdd;
    }
.source p.exc {
    background: #eeeeee;
    }
</style>
</head>
<body>
<table cellspacing='0' cellpadding='0'>
<tr>
<td class='linenos' valign='top'>
    {% for line in lines %}
    <p class='{{line.class}}'>{{line.number}}</p>
    {% endfor %}
</td>
<td class='source' valign='top'>
    {% for line in lines %}
    <p class='{{line.class}}'>{{line.text.rstrip|escape|not_empty}}</p>
    {% endfor %}
</td>
</tr>
</table>
</body>
</html>
"""
