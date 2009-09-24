def html_it():
    """Run coverage and make an XML report for a."""
    import coverage
    cov = coverage.coverage()
    cov.start()
    import a
    cov.stop()
    cov.xml_report(a, outfile=open("../xml/coverage.xml", 'w'))

import os
if not os.path.exists("xml"):
    os.makedirs("xml")

runfunc(html_it, rundir="src")

compare("xml", "gold_a_xml")
clean("xml")
