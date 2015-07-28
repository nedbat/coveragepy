# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

import sys

def html_it():
    """Run coverage.py and make an HTML report for isolatin1.py."""
    import coverage
    cov = coverage.Coverage()
    cov.start()
    import isolatin1            # pragma: nested
    cov.stop()                  # pragma: nested
    cov.html_report(isolatin1, directory="../html_isolatin1")

runfunc(html_it, rundir="src")

# HTML files will change often.  Check that the sizes are reasonable,
#   and check that certain key strings are in the output.
compare("gold_isolatin1", "html_isolatin1", size_within=10, file_pattern="*.html")
contains("html_isolatin1/isolatin1_py.html",
    '<span class="str">&quot;3&#215;4 = 12, &#247;2 = 6&#177;0&quot;</span>',
    )

clean("html_isolatin1")
