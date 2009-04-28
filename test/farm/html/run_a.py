def html_it():
    """Run coverage and make an HTML report for a."""
    import coverage
    cov = coverage.coverage()
    cov.start()
    import a
    cov.stop()
    cov.html_report(a, directory="../html")

runfunc(html_it, rundir="src")

# HTML files will change often.  Check that the sizes are reasonable,
#   and check that certain key strings are in the output.
compare("html", "gold_a", size_within=10)
contains("html/a.html",
    ">if 1 &lt; 2:<",
    "&nbsp; &nbsp; a = 3",
    "<span class='pc_cov'>67%</span>"
    )
contains("html/index.html",
    "<a href='a.html'>a</a>",
    "<span class='pc_cov'>67%</span>"
    )

clean("html")
