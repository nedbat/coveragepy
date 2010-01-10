"""Tests for process behavior of coverage.py."""

import os, sys
import coverage

sys.path.insert(0, os.path.split(__file__)[0]) # Force relative import for Py3k
from coveragetest import CoverageTest


class ProcessTest(CoverageTest):
    """Tests of the per-process behavior of coverage.py."""

    def number_of_data_files(self):
        """Return the number of coverage data files in this directory."""
        num = 0
        for f in os.listdir('.'):
            if f.startswith('.coverage.') or f == '.coverage':
                num += 1
        return num

    def testSaveOnExit(self):
        self.make_file("mycode.py", """\
            h = "Hello"
            w = "world"
            """)

        self.assertFalse(os.path.exists(".coverage"))
        self.run_command("coverage -x mycode.py")
        self.assertTrue(os.path.exists(".coverage"))

    def testEnvironment(self):
        # Checks that we can import modules from the test directory at all!
        self.make_file("mycode.py", """\
            import covmod1
            import covmodzip1
            a = 1
            print ('done')
            """)

        self.assertFalse(os.path.exists(".coverage"))
        out = self.run_command("coverage -x mycode.py")
        self.assertTrue(os.path.exists(".coverage"))
        self.assertEqual(out, 'done\n')

    def testCombineParallelData(self):
        self.make_file("b_or_c.py", """\
            import sys
            a = 1
            if sys.argv[1] == 'b':
                b = 1
            else:
                c = 1
            d = 1
            print ('done')
            """)

        out = self.run_command("coverage -x -p b_or_c.py b")
        self.assertEqual(out, 'done\n')
        self.assertFalse(os.path.exists(".coverage"))

        out = self.run_command("coverage -x -p b_or_c.py c")
        self.assertEqual(out, 'done\n')
        self.assertFalse(os.path.exists(".coverage"))

        # After two -p runs, there should be two .coverage.machine.123 files.
        self.assertEqual(self.number_of_data_files(), 2)

        # Combine the parallel coverage data files into .coverage .
        self.run_command("coverage -c")
        self.assertTrue(os.path.exists(".coverage"))

        # After combining, there should be only the .coverage file.
        self.assertEqual(self.number_of_data_files(), 1)

        # Read the coverage file and see that b_or_c.py has all 7 lines
        # executed.
        data = coverage.CoverageData()
        data.read_file(".coverage")
        self.assertEqual(data.summary()['b_or_c.py'], 7)

    def test_combine_with_rc(self):
        self.make_file("b_or_c.py", """\
            import sys
            a = 1
            if sys.argv[1] == 'b':
                b = 1
            else:
                c = 1
            d = 1
            print ('done')
            """)

        self.make_file(".coveragerc", """\
            [run]
            parallel = true
            """)

        out = self.run_command("coverage run b_or_c.py b")
        self.assertEqual(out, 'done\n')
        self.assertFalse(os.path.exists(".coverage"))

        out = self.run_command("coverage run b_or_c.py c")
        self.assertEqual(out, 'done\n')
        self.assertFalse(os.path.exists(".coverage"))

        # After two runs, there should be two .coverage.machine.123 files.
        self.assertEqual(self.number_of_data_files(), 2)

        # Combine the parallel coverage data files into .coverage .
        self.run_command("coverage combine")
        self.assertTrue(os.path.exists(".coverage"))
        self.assertTrue(os.path.exists(".coveragerc"))

        # After combining, there should be only the .coverage file.
        self.assertEqual(self.number_of_data_files(), 1)

        # Read the coverage file and see that b_or_c.py has all 7 lines
        # executed.
        data = coverage.CoverageData()
        data.read_file(".coverage")
        self.assertEqual(data.summary()['b_or_c.py'], 7)

    def test_missing_source_file(self):
        # Check what happens if the source is missing when reporting happens.
        self.make_file("fleeting.py", """\
            s = 'goodbye, cruel world!'
            """)

        self.run_command("coverage run fleeting.py")
        os.remove("fleeting.py")
        out = self.run_command("coverage html -d htmlcov")
        self.assertRegexpMatches(out, "No source for code: '.*fleeting.py'")
        self.assertFalse("Traceback" in out)

        # It happens that the code paths are different for *.py and other
        # files, so try again with no extension.
        self.make_file("fleeting", """\
            s = 'goodbye, cruel world!'
            """)

        self.run_command("coverage run fleeting")
        os.remove("fleeting")
        out = self.run_command("coverage html -d htmlcov")
        self.assertRegexpMatches(out, "No source for code: '.*fleeting'")
        self.assertFalse("Traceback" in out)

    def test_running_missing_file(self):
        out = self.run_command("coverage run xyzzy.py")
        self.assertRegexpMatches(out, "No file to run: .*xyzzy.py")
        self.assertFalse("Traceback" in out)
