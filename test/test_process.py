"""Tests for process behavior of coverage.py."""

import os, sys, textwrap
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

    def test_save_on_exit(self):
        self.make_file("mycode.py", """\
            h = "Hello"
            w = "world"
            """)

        self.assert_doesnt_exist(".coverage")
        self.run_command("coverage -x mycode.py")
        self.assert_exists(".coverage")

    def test_environment(self):
        # Checks that we can import modules from the test directory at all!
        self.make_file("mycode.py", """\
            import covmod1
            import covmodzip1
            a = 1
            print ('done')
            """)

        self.assert_doesnt_exist(".coverage")
        out = self.run_command("coverage -x mycode.py")
        self.assert_exists(".coverage")
        self.assertEqual(out, 'done\n')

    def test_combine_parallel_data(self):
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
        self.assert_doesnt_exist(".coverage")

        out = self.run_command("coverage -x -p b_or_c.py c")
        self.assertEqual(out, 'done\n')
        self.assert_doesnt_exist(".coverage")

        # After two -p runs, there should be two .coverage.machine.123 files.
        self.assertEqual(self.number_of_data_files(), 2)

        # Combine the parallel coverage data files into .coverage .
        self.run_command("coverage -c")
        self.assert_exists(".coverage")

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
        self.assert_doesnt_exist(".coverage")

        out = self.run_command("coverage run b_or_c.py c")
        self.assertEqual(out, 'done\n')
        self.assert_doesnt_exist(".coverage")

        # After two runs, there should be two .coverage.machine.123 files.
        self.assertEqual(self.number_of_data_files(), 2)

        # Combine the parallel coverage data files into .coverage .
        self.run_command("coverage combine")
        self.assert_exists(".coverage")
        self.assert_exists(".coveragerc")

        # After combining, there should be only the .coverage file.
        self.assertEqual(self.number_of_data_files(), 1)

        # Read the coverage file and see that b_or_c.py has all 7 lines
        # executed.
        data = coverage.CoverageData()
        data.read_file(".coverage")
        self.assertEqual(data.summary()['b_or_c.py'], 7)

        # Reporting should still work even with the .rc file
        out = self.run_command("coverage report")
        self.assertMultiLineEqual(out, textwrap.dedent("""\
            Name     Stmts   Miss  Cover
            ----------------------------
            b_or_c       7      0   100%
            """))

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
        status, out = self.run_command_status("coverage html -d htmlcov", 1)
        self.assertRegexpMatches(out, "No source for code: '.*fleeting'")
        self.assertFalse("Traceback" in out)
        self.assertEqual(status, 1)

    def test_running_missing_file(self):
        status, out = self.run_command_status("coverage run xyzzy.py", 1)
        self.assertRegexpMatches(out, "No file to run: .*xyzzy.py")
        self.assertFalse("Traceback" in out)
        self.assertEqual(status, 1)

    def test_code_throws(self):
        self.make_file("throw.py", """\
            def f1():
                raise Exception("hey!")

            def f2():
                f1()

            f2()
            """)

        # The important thing is for "coverage run" and "python" to report the
        # same traceback.
        status, out = self.run_command_status("coverage run throw.py", 1)
        out2 = self.run_command("python throw.py")
        self.assertMultiLineEqual(out, out2)

        # But also make sure that the output is what we expect.
        self.assertTrue('File "throw.py", line 5, in f2' in out)
        self.assertTrue('raise Exception("hey!")' in out)
        self.assertFalse('coverage' in out)
        self.assertEqual(status, 1)

    def test_code_exits(self):
        self.make_file("exit.py", """\
            import sys
            def f1():
                print("about to exit..")
                sys.exit(17)

            def f2():
                f1()

            f2()
            """)

        # The important thing is for "coverage run" and "python" to have the
        # same output.  No traceback.
        status, out = self.run_command_status("coverage run exit.py", 17)
        status2, out2 = self.run_command_status("python exit.py", 17)
        self.assertMultiLineEqual(out, out2)
        self.assertMultiLineEqual(out, "about to exit..\n")
        self.assertEqual(status, status2)
        self.assertEqual(status, 17)

    def test_code_exits_no_arg(self):
        self.make_file("exit_none.py", """\
            import sys
            def f1():
                print("about to exit quietly..")
                sys.exit()

            f1()
            """)
        status, out = self.run_command_status("coverage run exit_none.py", 0)
        status2, out2 = self.run_command_status("python exit_none.py", 0)
        self.assertMultiLineEqual(out, out2)
        self.assertMultiLineEqual(out, "about to exit quietly..\n")
        self.assertEqual(status, status2)
        self.assertEqual(status, 0)


    if hasattr(os, 'fork'):
        def test_fork(self):
            self.make_file("fork.py", """\
                import os

                def child():
                    print('Child!')

                def main():
                    ret = os.fork()

                    if ret == 0:
                        child()
                    else:
                        os.waitpid(ret, 0)

                main()
                """)

            out = self.run_command("coverage run -p fork.py")
            self.assertEqual(out, 'Child!\n')
            self.assert_doesnt_exist(".coverage")

            # After running the forking program, there should be two
            # .coverage.machine.123 files.
            self.assertEqual(self.number_of_data_files(), 2)

            # Combine the parallel coverage data files into .coverage .
            self.run_command("coverage -c")
            self.assert_exists(".coverage")

            # After combining, there should be only the .coverage file.
            self.assertEqual(self.number_of_data_files(), 1)

            # Read the coverage file and see that b_or_c.py has all 7 lines
            # executed.
            data = coverage.CoverageData()
            data.read_file(".coverage")
            self.assertEqual(data.summary()['fork.py'], 9)

    def test_warnings(self):
        self.make_file("hello.py", """\
            import sys, os
            print("Hello")
            """)
        out = self.run_command("coverage run --source=sys,xyzzy,quux hello.py")

        self.assertTrue("Hello\n" in out)
        self.assertTrue(textwrap.dedent("""\
            Coverage.py warning: Module sys has no python source.
            Coverage.py warning: Module xyzzy was never imported.
            Coverage.py warning: Module quux was never imported.
            Coverage.py warning: No data was collected.
            """) in out)

    def test_warnings_if_never_run(self):
        out = self.run_command("coverage run i_dont_exist.py")
        self.assertTrue("No file to run: 'i_dont_exist.py'" in out)
        self.assertTrue("warning" not in out)

        out = self.run_command("coverage run -m no_such_module")
        self.assertTrue("No module named no_such_module" in out)
        self.assertTrue("warning" not in out)

