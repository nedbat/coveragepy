# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

source_path = None

def xml_it():
    """Run coverage.py and make an XML report for y."""
    import coverage, coverage.files
    cov = coverage.Coverage(branch=True)
    cov.start()
    import y            # pragma: nested
    cov.stop()          # pragma: nested
    cov.xml_report(y, outfile="../xml_branch/coverage.xml")
    global source_path
    source_path = coverage.files.relative_directory().rstrip('/')

runfunc(xml_it, rundir="src")

compare("gold_y_xml_branch", "xml_branch", scrubs=[
    (r' timestamp="\d+"', ' timestamp="TIMESTAMP"'),
    (r' version="[-.\w]+"', ' version="VERSION"'),
    (r'<source>\s*.*?\s*</source>', '<source>%s</source>' % source_path),
    (r'/coverage.readthedocs.org/?[-.\w/]*', '/coverage.readthedocs.org/VER'),
    ])
clean("xml_branch")
