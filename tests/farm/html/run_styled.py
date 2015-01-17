def html_it():
    """Run coverage and make an HTML report for a."""
    import coverage
    cov = coverage.coverage()
    cov.start()
    import a            # pragma: nested
    cov.stop()          # pragma: nested
    cov.html_report(a, directory="../html_styled", extra_css="extra.css")

runfunc(html_it, rundir="src")

# HTML files will change often.  Check that the sizes are reasonable,
#   and check that certain key strings are in the output.
compare("gold_styled", "html_styled", size_within=10, file_pattern="*.html")
compare("gold_styled", "html_styled", size_within=10, file_pattern="*.css")
contains("html_styled/a_py.html",
    "<link rel='stylesheet' href='extra.css' type='text/css'>",
    "<span class='key'>if</span> <span class='num'>1</span> <span class='op'>&lt;</span> <span class='num'>2</span>",
    "&nbsp; &nbsp; <span class='nam'>a</span> <span class='op'>=</span> <span class='num'>3</span>",
    "<span class='pc_cov'>67%</span>"
    )
contains("html_styled/index.html",
    "<link rel='stylesheet' href='extra.css' type='text/css'>",
    "<a href='a_py.html'>a.py</a>",
    "<span class='pc_cov'>67%</span>"
    )

clean("html_styled")
