def html_it():
    """Run coverage and make an HTML report for tabbed."""
    import coverage
    cov = coverage.coverage()
    cov.start()
    import tabbed           # pragma: nested
    cov.stop()              # pragma: nested
    cov.html_report(tabbed, directory="../html_tabbed")

runfunc(html_it, rundir="src")

# Editors like to change things, make sure our source file still has tabs.
contains("src/tabbed.py", "\tif x:\t\t\t\t\t# look nice")

contains("html_tabbed/tabbed_py.html",
    '>&nbsp; &nbsp; &nbsp; &nbsp; <span class="key">if</span> '
    '<span class="nam">x</span><span class="op">:</span>'
    '&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; '
    '&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;&nbsp; '
    '<span class="com"># look nice</span>'
    )

doesnt_contain("html_tabbed/tabbed_py.html", "\t")
clean("html_tabbed")
