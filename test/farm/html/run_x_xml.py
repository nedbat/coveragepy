def html_it():
    """Run coverage and make an XML report for x."""
    import coverage
    cov = coverage.coverage()
    cov.start()
    import x
    cov.stop()
    cov.xml_report(x, outfile="../xml/coverage.xml")

import os
if not os.path.exists("xml"):
    os.makedirs("xml")

runfunc(html_it, rundir="src")

compare("gold_x_xml", "xml", scrubs=[
    (r' timestamp="\d+"', ' timestamp="TIMESTAMP"'),
    (r' version="[-.\w]+"', ' version="VERSION"'),
    ])
clean("xml")
