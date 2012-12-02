def html_it():
    """Run coverage and make an HTML report for main."""
    import coverage
    cov = coverage.coverage(config_file="omit4.ini")
    cov.start()
    import main         # pragma: nested
    cov.stop()          # pragma: nested
    cov.html_report(directory="../html_omit_4")

runfunc(html_it, rundir="src")
compare("gold_omit_4", "html_omit_4", size_within=10, file_pattern="*.html")
clean("html_omit_4")
