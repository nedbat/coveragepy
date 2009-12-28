def html_it():
    """Run coverage and make an HTML report for a."""
    import coverage
    cov = coverage.coverage()
    cov.start()
    import a
    cov.stop()
    cov.html_report(a, directory="../html_a")

runfunc(html_it, rundir="src")

# HTML files will change often.  Check that the sizes are reasonable,
#   and check that certain key strings are in the output.
compare("gold_a", "html_a", size_within=10, file_pattern="*.html")
contains("html_a/a.html",
    "<span class='key'>if</span> <span class='num'>1</span> <span class='op'>&lt;</span> <span class='num'>2</span>",
    "&nbsp; &nbsp; <span class='nam'>a</span> <span class='op'>=</span> <span class='num'>3</span>",
    "<span class='pc_cov'>67%</span>"
    )
contains("html_a/index.html",
    "<a href='a.html'>a</a>",
    "<span class='pc_cov'>67%</span>"
    )

clean("html_a")
