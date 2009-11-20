"""
Write and report coverage data with 'coverage.py'. 
"""
import py

coverage = py.test.importorskip("coverage")

def pytest_configure(config):
    # Load the runner and start it up
    from coverage.runner import CoverageTestWrapper
    
    config.coverage = CoverageTestWrapper(config.option)
    config.coverage.start()

def pytest_terminal_summary(terminalreporter):
    # Finished the tests start processing the coverage
    config = terminalreporter.config
    tw = terminalreporter._tw
    tw.sep('-', 'coverage')
    tw.line('Processing Coverage...')
    
    # finish up with coverage
    config.coverage.finish()

def pytest_addoption(parser):
    """
    Get all the options from the coverage.runner and import them
    """
    from coverage.runner import Options
    
    group = parser.getgroup('Coverage options')
    # Loop the coverage options and append them to the plugin options
    options = [a for a in dir(Options) if not a.startswith('_')]
    for option in options:
        opt = getattr(Options, option)
        group._addoption_instance(opt, shortupper=True)

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

def test_functional(testdir):
    py.test.importorskip("coverage")
    testdir.plugins.append("coverage")
    testdir.makepyfile("""
        def f():    
            x = 42
        def test_whatever():
            pass
        """)
    result = testdir.runpytest()
    assert result.ret == 0
    assert result.stdout.fnmatch_lines([
        '*Processing Coverage*'
        ])