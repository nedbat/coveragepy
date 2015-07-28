# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

def html_it():
    """Run coverage.py and make an HTML report for main."""
    import coverage
    cov = coverage.Coverage(config_file="omit5.ini", include=["./*"])
    cov.start()
    import main         # pragma: nested
    cov.stop()          # pragma: nested
    cov.html_report()

runfunc(html_it, rundir="src")
compare("gold_omit_5", "html_omit_5", size_within=10, file_pattern="*.html")
clean("html_omit_5")
