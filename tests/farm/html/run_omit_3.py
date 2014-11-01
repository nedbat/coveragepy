def html_it():
    """Run coverage and make an HTML report for main."""
    import coverage
    cov = coverage.coverage(include=["./*"])
    cov.start()
    import main         # pragma: nested
    cov.stop()          # pragma: nested
    cov.html_report(directory="../html_omit_3", omit=["m1.py", "m2.py"])

runfunc(html_it, rundir="src")
compare("gold_omit_3", "html_omit_3", size_within=10, file_pattern="*.html")
clean("html_omit_3")
