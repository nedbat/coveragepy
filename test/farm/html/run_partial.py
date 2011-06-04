import sys

def html_it():
    """Run coverage and make an HTML report for partial."""
    import coverage
    cov = coverage.coverage(branch=True)
    cov.start()
    import partial
    cov.stop()
    cov.html_report(partial, directory="../html_partial")

runfunc(html_it, rundir="src")

# HTML files will change often.  Check that the sizes are reasonable,
#   and check that certain key strings are in the output.
compare("gold_partial", "html_partial", size_within=10, file_pattern="*.html")
contains("html_partial/partial.html",
    "<p id='t5' class='stm run hide_run'>",
    "<p id='t8' class='stm run hide_run'>",
    "<p id='t11' class='stm run hide_run'>",
    # The "if 0" and "if 1" statements are optimized away.
    "<p id='t14' class='pln'>",
    )
contains("html_partial/index.html",
    "<a href='partial.html'>partial</a>",
    )
if sys.version_info >= (2, 4):
    contains("html_partial/index.html",
        "<span class='pc_cov'>100%</span>"
        )

clean("html_partial")
