"""HTML reporting for coverage.py"""

import os
from coverage import __version__
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
    return (t
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
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
<title>Coverage for {{cu.name|escape}}</title>
<style>
html, body {
    margin: 0;
    padding: 0;
    font-size: 85%;
    }
p {
    margin: 0;
    padding: 0;
    }
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
    font-variant: italic;
    }
    
.content {
    padding: 1em;
    }
    
a.nav {
    text-decoration: none;
    color: inherit;
    }
a.nav:hover {
    text-decoration: underline;
    color: inherit;
    }

.linenos {
    background: #eeeeee;    
    }
.linenos p {
    text-align: right;
    margin: 0;
    padding: 0 .5em 0 .5em;
    color: #999999;
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
        <p>Coverage for <b>{{cu.filename|escape}}</b></p>
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
