"""HTML reporting for coverage.py"""

import os
from coverage import __version__    # pylint: disable-msg=W0611
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

# Templates

# For making line numbers and text different fonts:
# http://24ways.org/2006/compose-to-a-vertical-rhythm

SOURCE = """\
<!doctype html PUBLIC "-//W3C//DTD html 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
<title>Coverage for {{cu.name|escape}}</title>
<style>
/* Page-wide styles */
html, body, p, td {
    margin: 0;
    padding: 0;
    }

/* Set baseline grid to 14 pt. */
body {
    font-size: .875em; /* 14/16 */
    }
  
html>body {
    font-size: 14px;
    }    

/* Set base font size to 12/14 */
p {
    font-size: .85714em;        /* 12/14 */
    line-height: 1.16667em;     /* 14/12 */
    }

a.nav {
    text-decoration: none;
    color: inherit;
    }
a.nav:hover {
    text-decoration: underline;
    color: inherit;
    }

/* Page structure */
#header {
    background: #ffd472;
    width: 100%;
    font-family: verdana, sans-serif;
    }

#source {
    padding: 1em;
    font-family: "courier new", monospace;
    }

#footer {
    background: #ffe9b8;
    font-size: 85%;
    font-family: verdana, sans-serif;
    color: #666666;
    font-style: italic;
    }

/* Header styles */
.content {
    padding: 1em;
    }
    
#file_stats {
    float: right;
    }

.stats .number {
    text-align: right;
    font-weight: bold;
    }

/* Source file styles */
.linenos {
    background: #eeeeee;    
    }
.linenos p {
    text-align: right;
    margin: 0;
    padding: 0 .5em;
    color: #999999;
    font-size: .75em;       /* 9/12 */
    line-height: 1.3333em;  /* 12/9, why isn't it 14/9? */
    }
td.text {
    width: 100%;
    }
.text p {
    margin: 0;
    padding: 0 0 0 .5em;
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

.text p.mis {
    background: #ffdddd;
    }
.text p.run {
    background: #ddffdd;
    }
.text p.exc {
    background: #eeeeee;
    }
</style>
</head>
<body>
<div id='header'>
    <div class='content'>
        <div id='file_stats'>
            <table class='stats'>
            <tr><td class='label'>Lines</td><td class='number'>{{n_lin}}</td></tr>
            <tr><td class='label'>Statements</td><td class='number'>{{n_stm}}</td></tr>
            <tr><td class='label'>Excluded</td><td class='number'>{{n_exc}}</td></tr>
            <tr><td class='label'>Missing</td><td class='number'>{{n_mis}}</td></tr>
            </table>
        </div>
        <p>Coverage for <b>{{cu.filename|escape}}</b>:
            <span class='pc_cov'>{{pc_cov|format_pct}}%</span>
        </p>
        <div style='clear:both'></div>
    </div>
</div>

<div id='source'>
<table cellspacing='0' cellpadding='0'>
<tr>
<td class='linenos' valign='top'>
    {% for line in lines %}
    <p class='{{line.class}}'>{{line.number}}</p>
    {% endfor %}
</td>
<td class='text' valign='top'>
    {% for line in lines %}
    <p class='{{line.class}}'>{{line.text.rstrip|escape|not_empty}}</p>
    {% endfor %}
</td>
</tr>
</table>
</div>

<div id='footer'>
    <div class='content'>
        <p>
            <a class='nav' href='http://bitbucket.org/ned/coveragepy/'>coverage.py v{{__version__}}</a>
        </p>
    </div>
</div>

</body>
</html>
"""
