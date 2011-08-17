def html_it():
    """Run coverage with branches and make an HTML report for b."""
    import coverage
    cov = coverage.coverage(branch=True)
    cov.start()
    import b
    cov.stop()
    cov.html_report(b, directory="../html_b_branch")

runfunc(html_it, rundir="src")

# HTML files will change often.  Check that the sizes are reasonable,
#   and check that certain key strings are in the output.
compare("gold_b_branch", "html_b_branch", size_within=10, file_pattern="*.html")
contains("html_b_branch/b.html",
    "<span class='key'>if</span> <span class='nam'>x</span> <span class='op'>&lt;</span> <span class='num'>2</span>",
    "&nbsp; &nbsp; <span class='nam'>a</span> <span class='op'>=</span> <span class='num'>3</span>",
    "<span class='pc_cov'>70%</span>",
    "<span class='annotate' title='no jump to this line number'>8</span>",
    "<span class='annotate' title='no jump to this line number'>exit</span>",
    "<span class='annotate' title='no jumps to these line numbers'>23&nbsp;&nbsp; 25</span>",
    )
contains("html_b_branch/index.html",
    "<a href='b.html'>b</a>",
    "<span class='pc_cov'>70%</span>"
    )

clean("html_b_branch")
