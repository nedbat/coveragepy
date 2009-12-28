def html_it():
    """Run coverage and make an XML report for x."""
    import coverage
    cov = coverage.coverage()
    cov.start()
    import a
    reload(a) # Because other test files import a, we have to reload to run it.
    cov.stop()
    cov.xml_report(a, outfile="../xml/coverage.xml")

import os
if not os.path.exists("xml"):
    os.makedirs("xml")

runfunc(html_it, rundir="src")

compare("gold_x_xml", "xml", scrubs=[
    (r' timestamp="\d+"', ' timestamp="TIMESTAMP"'),
    (r' version="[-.\w]+"', ' version="VERSION"'),
    ])
clean("xml")
