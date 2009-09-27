def html_it():
    """Run coverage and make an HTML report for everything."""
    import coverage
    cov = coverage.coverage()
    cov.start()
    import here
    cov.stop()
    cov.html_report(directory="../otherhtml")

runfunc(html_it, rundir="src", addtopath="../othersrc")

# HTML files will change often.  Check that the sizes are reasonable,
#   and check that certain key strings are in the output.
compare("gold_other", "otherhtml", size_within=10)
contains("otherhtml/index.html",
    "<a href='here.html'>here</a>",
    "other.html'>", "other</a>",
    )

clean("otherhtml")
