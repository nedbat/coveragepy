def html_it():
    """Run coverage and make an HTML report for tabbed."""
    import coverage
    cov = coverage.coverage()
    cov.start()
    import tabbed
    cov.stop()
    cov.html_report(tabbed, directory="../html")

runfunc(html_it, rundir="src")

# Editors like to change things, make sure our source file still has tabs.
contains("src/tabbed.py", "\tif x:\t\t\t\t\t\t# look nice")

contains("html/tabbed.html",
    ">&nbsp; &nbsp; <span class='key'>if</span> <span class='nam'>x</span>"
    "<span class='op'>:</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;"
    " &nbsp; &nbsp; &nbsp; &nbsp;&nbsp; <span class='com'># look nice</span>"
    )

doesnt_contain("html/tabbed.html", "\t")
clean("html")
