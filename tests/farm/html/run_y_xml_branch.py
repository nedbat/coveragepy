def xml_it():
    """Run coverage and make an XML report for y."""
    import coverage
    cov = coverage.coverage(branch=True)
    cov.start()
    import y            # pragma: nested
    cov.stop()          # pragma: nested
    cov.xml_report(y, outfile="../xml_branch/coverage.xml")

import os
if not os.path.exists("xml_branch"):
    os.makedirs("xml_branch")

runfunc(xml_it, rundir="src")

compare("gold_y_xml_branch", "xml_branch", scrubs=[
    (r' timestamp="\d+"', ' timestamp="TIMESTAMP"'),
    (r' version="[-.\w]+"', ' version="VERSION"'),
    (r'<source>(.*)</source>', '<source></source>'),
    (r'/code/coverage/?[-.\w]*', '/code/coverage/VER'),
    ])
clean("xml_branch")
