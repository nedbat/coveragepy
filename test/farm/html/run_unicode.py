import sys

def html_it():
    """Run coverage and make an HTML report for unicode.py."""
    import coverage
    cov = coverage.coverage()
    cov.start()
    import unicode          # pragma: nested
    cov.stop()              # pragma: nested
    cov.html_report(unicode, directory="../html_unicode")

runfunc(html_it, rundir="src")

# HTML files will change often.  Check that the sizes are reasonable,
#   and check that certain key strings are in the output.
compare("gold_unicode", "html_unicode", size_within=10, file_pattern="*.html")
contains("html_unicode/unicode.html",
    "<span class='str'>&quot;&#654;d&#729;&#477;b&#592;&#633;&#477;&#652;o&#596;&quot;</span>",
    )

if sys.maxunicode == 65535:
    contains("html_unicode/unicode.html",
        "<span class='str'>&quot;db40,dd00: x&#56128;&#56576;&quot;</span>",
        )
else:
    contains("html_unicode/unicode.html",
        "<span class='str'>&quot;db40,dd00: x&#917760;&quot;</span>",
        )

clean("html_unicode")
