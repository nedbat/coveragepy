def html_it():
    """Run coverage and make an XML report for a."""
    import coverage
    cov = coverage.coverage(config_file="run_a_xml_2.ini")
    cov.start()
    import a
    cov.stop()
    cov.xml_report(a)

import os
if not os.path.exists("xml_2"):
    os.makedirs("xml_2")

runfunc(html_it, rundir="src")

compare("gold_x_xml", "xml_2", scrubs=[
    (r' timestamp="\d+"', ' timestamp="TIMESTAMP"'),
    (r' version="[-.\w]+"', ' version="VERSION"'),
    (r'/code/coverage/?[-.\w]*', '/code/coverage/VER'),
    ])
clean("xml_2")
