def html_it():
    """Run coverage and make an HTML report for everything."""
    import coverage
    cov = coverage.coverage(include=["./*", "../othersrc/*"])
    cov.start()
    import here         # pragma: nested
    cov.stop()          # pragma: nested
    cov.html_report(directory="../html_other")

runfunc(html_it, rundir="src", addtopath="../othersrc")

# Different platforms will name the "other" file differently. Rename it
import os, glob

for p in glob.glob("html_other/*_other.html"):
    os.rename(p, "html_other/blah_blah_other.html")

# HTML files will change often.  Check that the sizes are reasonable,
#   and check that certain key strings are in the output.
compare("gold_other", "html_other", size_within=10, file_pattern="*.html")
contains("html_other/index.html",
    "<a href='here.html'>here</a>",
    "other.html'>", "other</a>",
    )

clean("html_other")
