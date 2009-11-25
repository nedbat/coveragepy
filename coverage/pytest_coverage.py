"""
Write and report coverage data with 'coverage.py'. 
"""
import py
import coverage

def pytest_addoption(parser):
    """
    Get all the options from the coverage.runner and import them
    """
    from coverage.runner import options
    group = parser.getgroup('Coverage options')
    for opt in options:
        group._addoption_instance(opt)

def pytest_configure(config):
    # Load the runner and start it up
    if config.getvalue("cover_actions"):
        config.pluginmanager.register(DoCover(config), "do_coverage")

class DoCover:
    def __init__(self, config):
        self.config = config

    def pytest_sessionstart(self):
        from coverage.runner import CoverageTestWrapper
        self.coverage = CoverageTestWrapper(self.config.option)
        # XXX maybe better to start/suspend/resume coverage
        # for each single test item
        self.coverage.start()

    def pytest_terminal_summary(self, terminalreporter):
        # Finished the tests start processing the coverage
        config = terminalreporter.config
        tw = terminalreporter._tw
        tw.sep('-', 'coverage')
        tw.line('Processing Coverage...')
        self.coverage.finish()
       

# Monkey patch omit_filter to use regex patterns for file omits
def omit_filter(omit_prefixes, code_units):
    import re
    exclude_patterns = [re.compile(line.strip()) for line in omit_prefixes if line and not line.startswith('#')]
    filtered = []
    for cu in code_units:
        skip = False
        for pattern in exclude_patterns:
            if pattern.search(cu.filename):
                skip = True
                break
            
        if not skip:
            filtered.append(cu)
    return filtered

coverage.codeunit.omit_filter = omit_filter

pytest_plugins = ['pytester']
def test_functional(testdir):
    testdir.makepyfile("""
        def f():    
            x = 42
        def test_whatever():
            pass
        """)
    result = testdir.runpytest("--cover-action=annotate")
    assert result.ret == 0
    assert result.stdout.fnmatch_lines([
        '*Processing Coverage*'
        ])
    coveragefile = testdir.tmpdir.join(".coverage")
    assert coveragefile.check()
    # XXX try loading it? 
