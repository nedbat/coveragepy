# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

def html_it():
    """Run coverage.py with branches and make an HTML report for b."""
    import coverage
    cov = coverage.Coverage(branch=True)
    cov.start()
    import b            # pragma: nested
    cov.stop()          # pragma: nested
    cov.html_report(b, directory="../html_b_branch")

runfunc(html_it, rundir="src")

# HTML files will change often.  Check that the sizes are reasonable,
#   and check that certain key strings are in the output.
compare("gold_b_branch", "html_b_branch", size_within=10, file_pattern="*.html")
contains("html_b_branch/b_py.html",
    '<span class="key">if</span> <span class="nam">x</span> <span class="op">&lt;</span> <span class="num">2</span>',
    '&nbsp; &nbsp; <span class="nam">a</span> <span class="op">=</span> <span class="num">3</span>',
    '<span class="pc_cov">70%</span>',
    '<span class="annotate" title="Line 8 was executed, but never jumped to line 11">8&#x202F;&#x219B;&#x202F;11 [?]</span>',
    '<span class="annotate" title="Line 17 was executed, but never jumped to the function exit">17&#x202F;&#x219B;&#x202F;exit [?]</span>',
    '<span class="annotate" title="Line 25 was executed, but never jumped to line 26 or line 28">25&#x202F;&#x219B;&#x202F;26,&nbsp;&nbsp; 25&#x202F;&#x219B;&#x202F;28 [?]</span>',
    )
contains("html_b_branch/index.html",
    '<a href="b_py.html">b.py</a>',
    '<span class="pc_cov">70%</span>',
    '<td class="right" data-ratio="16 23">70%</td>',
    )

clean("html_b_branch")
