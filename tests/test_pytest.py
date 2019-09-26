import sqlite3

import pytest

pytest_plugins = 'pytester',

xdist_params = pytest.mark.parametrize('opts', [
    '',
    pytest.param('-n 1', marks=pytest.mark.skipif('sys.platform == "win32" and platform.python_implementation() == "PyPy"'))
], ids=['nodist', 'xdist'])


CONTEXTFUL_TESTS = '''\
import unittest

def test_one():
    assert 1 == 1

def test_two():
    assert 2 == 2

class OldStyleTests(unittest.TestCase):
    def setUp(self):
        self.three = 3
    def tearDown(self):
        self.three = None
    def test_three(self):
        assert self.three == 3
'''


@xdist_params
def test_contexts(testdir, opts):
    script = testdir.makepyfile(CONTEXTFUL_TESTS)
    result = testdir.runpytest('-vv', '-s',
                               '--cov=%s' % script.dirpath(),
                               '--cov-context=test',
                               script,
                               *opts.split()
                               )
    result.stdout.fnmatch_lines([
        'test_contexts* 100%*',
    ])
    con = sqlite3.connect(".coverage")
    cur = con.cursor()
    contexts = set(r[0] for r in cur.execute("select context from context"))
    assert contexts == {
        '',
        'test_contexts.py::test_two|run',
        'test_contexts.py::test_one|run',
        'test_contexts.py::OldStyleTests::test_three|run',
    }
