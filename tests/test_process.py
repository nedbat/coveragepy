"""Tests for process behavior of coverage.py."""

import glob
import os
import os.path
import sys
import textwrap

import coverage
from coverage import env

from tests.coveragetest import CoverageTest

HERE = os.path.dirname(__file__)


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
        self.run_command("coverage run mycode.py")
        self.assert_exists(".coverage")

    def test_environment(self):
        # Checks that we can import modules from the test directory at all!
        self.make_file("mycode.py", """\
            import covmod1
            import covmodzip1
            a = 1
            print('done')
            """)

        self.assert_doesnt_exist(".coverage")
        out = self.run_command("coverage run mycode.py")
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
            print('done')
            """)

        out = self.run_command("coverage run -p b_or_c.py b")
        self.assertEqual(out, 'done\n')
        self.assert_doesnt_exist(".coverage")

        out = self.run_command("coverage run -p b_or_c.py c")
        self.assertEqual(out, 'done\n')
        self.assert_doesnt_exist(".coverage")

        # After two -p runs, there should be two .coverage.machine.123 files.
        self.assertEqual(self.number_of_data_files(), 2)

        # Combine the parallel coverage data files into .coverage .
        self.run_command("coverage combine")
        self.assert_exists(".coverage")

        # After combining, there should be only the .coverage file.
        self.assertEqual(self.number_of_data_files(), 1)

        # Read the coverage file and see that b_or_c.py has all 7 lines
        # executed.
        data = coverage.CoverageData()
        data.read_file(".coverage")
        self.assertEqual(data.summary()['b_or_c.py'], 7)

    def test_combine_parallel_data_in_two_steps(self):
        self.make_file("b_or_c.py", """\
            import sys
            a = 1
            if sys.argv[1] == 'b':
                b = 1
            else:
                c = 1
            d = 1
            print('done')
            """)

        out = self.run_command("coverage run -p b_or_c.py b")
        self.assertEqual(out, 'done\n')
        self.assert_doesnt_exist(".coverage")
        self.assertEqual(self.number_of_data_files(), 1)

        # Combine the (one) parallel coverage data file into .coverage .
        self.run_command("coverage combine")
        self.assert_exists(".coverage")
        self.assertEqual(self.number_of_data_files(), 1)

        out = self.run_command("coverage run --append -p b_or_c.py c")
        self.assertEqual(out, 'done\n')
        self.assert_exists(".coverage")
        self.assertEqual(self.number_of_data_files(), 2)

        # Combine the parallel coverage data files into .coverage .
        self.run_command("coverage combine")
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
            print('done')
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
            Name        Stmts   Miss  Cover
            -------------------------------
            b_or_c.py       7      0   100%
            """))

    def test_combine_with_aliases(self):
        self.make_file("d1/x.py", """\
            a = 1
            b = 2
            print("%s %s" % (a, b))
            """)

        self.make_file("d2/x.py", """\
            # 1
            # 2
            # 3
            c = 4
            d = 5
            print("%s %s" % (c, d))
            """)

        self.make_file(".coveragerc", """\
            [run]
            parallel = True

            [paths]
            source =
                src
                */d1
                */d2
            """)

        out = self.run_command("coverage run " + os.path.normpath("d1/x.py"))
        self.assertEqual(out, '1 2\n')
        out = self.run_command("coverage run " + os.path.normpath("d2/x.py"))
        self.assertEqual(out, '4 5\n')

        self.assertEqual(self.number_of_data_files(), 2)

        self.run_command("coverage combine")
        self.assert_exists(".coverage")

        # After combining, there should be only the .coverage file.
        self.assertEqual(self.number_of_data_files(), 1)

        # Read the coverage data file and see that the two different x.py
        # files have been combined together.
        data = coverage.CoverageData()
        data.read_file(".coverage")
        summary = data.summary(fullpath=True)
        self.assertEqual(len(summary), 1)
        actual = os.path.normcase(os.path.abspath(list(summary.keys())[0]))
        expected = os.path.normcase(os.path.abspath('src/x.py'))
        self.assertEqual(actual, expected)
        self.assertEqual(list(summary.values())[0], 6)

    def test_missing_source_file(self):
        # Check what happens if the source is missing when reporting happens.
        self.make_file("fleeting.py", """\
            s = 'goodbye, cruel world!'
            """)

        self.run_command("coverage run fleeting.py")
        os.remove("fleeting.py")
        out = self.run_command("coverage html -d htmlcov")
        self.assertRegex(out, "No source for code: '.*fleeting.py'")
        self.assertNotIn("Traceback", out)

        # It happens that the code paths are different for *.py and other
        # files, so try again with no extension.
        self.make_file("fleeting", """\
            s = 'goodbye, cruel world!'
            """)

        self.run_command("coverage run fleeting")
        os.remove("fleeting")
        status, out = self.run_command_status("coverage html -d htmlcov")
        self.assertRegex(out, "No source for code: '.*fleeting'")
        self.assertNotIn("Traceback", out)
        self.assertEqual(status, 1)

    def test_running_missing_file(self):
        status, out = self.run_command_status("coverage run xyzzy.py")
        self.assertRegex(out, "No file to run: .*xyzzy.py")
        self.assertNotIn("raceback", out)
        self.assertNotIn("rror", out)
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
        status, out = self.run_command_status("coverage run throw.py")
        out2 = self.run_command("python throw.py")
        if env.PYPY:
            # Pypy has an extra frame in the traceback for some reason
            lines2 = out2.splitlines()
            out2 = "".join(l+"\n" for l in lines2 if "toplevel" not in l)
        self.assertMultiLineEqual(out, out2)

        # But also make sure that the output is what we expect.
        self.assertIn('File "throw.py", line 5, in f2', out)
        self.assertIn('raise Exception("hey!")', out)
        self.assertNotIn('coverage', out)
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
        status, out = self.run_command_status("coverage run exit.py")
        status2, out2 = self.run_command_status("python exit.py")
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
        status, out = self.run_command_status("coverage run exit_none.py")
        status2, out2 = self.run_command_status("python exit_none.py")
        self.assertMultiLineEqual(out, out2)
        self.assertMultiLineEqual(out, "about to exit quietly..\n")
        self.assertEqual(status, status2)
        self.assertEqual(status, 0)

    def test_coverage_run_is_like_python(self):
        tryfile = os.path.join(HERE, "try_execfile.py")
        with open(tryfile) as f:
            self.make_file("run_me.py", f.read())
        out_cov = self.run_command("coverage run run_me.py")
        out_py = self.run_command("python run_me.py")
        self.assertMultiLineEqual(out_cov, out_py)

    def test_coverage_run_dashm_is_like_python_dashm(self):
        # These -m commands assume the coverage tree is on the path.
        out_cov = self.run_command("coverage run -m tests.try_execfile")
        out_py = self.run_command("python -m tests.try_execfile")
        self.assertMultiLineEqual(out_cov, out_py)

    def test_coverage_run_dashm_equal_to_doubledashsource(self):
        """regression test for #328

        When imported by -m, a module's __name__ is __main__, but we need the
        --source machinery to know and respect the original name.
        """
        # These -m commands assume the coverage tree is on the path.
        out_cov = self.run_command(
            "coverage run --source tests.try_execfile -m tests.try_execfile"
        )
        out_py = self.run_command("python -m tests.try_execfile")
        self.assertMultiLineEqual(out_cov, out_py)

    def test_coverage_run_dashm_superset_of_doubledashsource(self):
        """Edge case: --source foo -m foo.bar"""
        # These -m commands assume the coverage tree is on the path.
        out_cov = self.run_command(
            "coverage run --source tests -m tests.try_execfile"
        )
        out_py = self.run_command("python -m tests.try_execfile")
        self.assertMultiLineEqual(out_cov, out_py)

        st, out = self.run_command_status("coverage report")
        self.assertEqual(st, 0)
        self.assertEqual(self.line_count(out), 6, out)

    def test_coverage_run_script_imports_doubledashsource(self):
        # This file imports try_execfile, which compiles it to .pyc, so the
        # first run will have __file__ == "try_execfile.py" and the second will
        # have __file__ == "try_execfile.pyc", which throws off the comparison.
        # Setting dont_write_bytecode True stops the compilation to .pyc and
        # keeps the test working.
        self.make_file("myscript", """\
            import sys; sys.dont_write_bytecode = True
            import tests.try_execfile
            """)

        # These -m commands assume the coverage tree is on the path.
        out_cov = self.run_command(
            "coverage run --source tests myscript"
        )
        out_py = self.run_command("python myscript")
        self.assertMultiLineEqual(out_cov, out_py)

        st, out = self.run_command_status("coverage report")
        self.assertEqual(st, 0)
        self.assertEqual(self.line_count(out), 6, out)

    def test_coverage_run_dashm_is_like_python_dashm_off_path(self):
        # https://bitbucket.org/ned/coveragepy/issue/242
        tryfile = os.path.join(HERE, "try_execfile.py")
        self.make_file("sub/__init__.py", "")
        with open(tryfile) as f:
            self.make_file("sub/run_me.py", f.read())
        out_cov = self.run_command("coverage run -m sub.run_me")
        out_py = self.run_command("python -m sub.run_me")
        self.assertMultiLineEqual(out_cov, out_py)

    def test_coverage_run_dashm_is_like_python_dashm_with__main__207(self):
        if sys.version_info < (2, 7):
            # Coverage isn't bug-for-bug compatible in the behavior of -m for
            # Pythons < 2.7
            self.skip("-m doesn't work the same < Python 2.7")
        # https://bitbucket.org/ned/coveragepy/issue/207
        self.make_file("package/__init__.py", "print('init')")
        self.make_file("package/__main__.py", "print('main')")
        out_cov = self.run_command("coverage run -m package")
        out_py = self.run_command("python -m package")
        self.assertMultiLineEqual(out_cov, out_py)

    def test_fork(self):
        if not hasattr(os, 'fork'):
            self.skip("Can't test os.fork since it doesn't exist.")

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
        self.run_command("coverage combine")
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

        self.assertIn("Hello\n", out)
        self.assertIn(textwrap.dedent("""\
            Coverage.py warning: Module sys has no Python source.
            Coverage.py warning: Module xyzzy was never imported.
            Coverage.py warning: Module quux was never imported.
            Coverage.py warning: No data was collected.
            """), out)

    def test_warnings_during_reporting(self):
        # While fixing issue #224, the warnings were being printed far too
        # often.  Make sure they're not any more.
        self.make_file("hello.py", """\
            import sys, os, the_other
            print("Hello")
            """)
        self.make_file("the_other.py", """\
            print("What?")
            """)
        self.make_file(".coveragerc", """\
            [run]
            source =
                .
                xyzzy
            """)

        self.run_command("coverage run hello.py")
        out = self.run_command("coverage html")
        self.assertEqual(out.count("Module xyzzy was never imported."), 0)

    def test_warnings_if_never_run(self):
        out = self.run_command("coverage run i_dont_exist.py")
        self.assertIn("No file to run: 'i_dont_exist.py'", out)
        self.assertNotIn("warning", out)
        self.assertNotIn("Exception", out)

        out = self.run_command("coverage run -m no_such_module")
        self.assertTrue(
            ("No module named no_such_module" in out) or
            ("No module named 'no_such_module'" in out)
            )
        self.assertNotIn("warning", out)
        self.assertNotIn("Exception", out)

    def test_warnings_trace_function_changed_with_threads(self):
        # https://bitbucket.org/ned/coveragepy/issue/164
        self.make_file("bug164.py", """\
            import threading
            import time

            class MyThread (threading.Thread):
                def run(self):
                    print("Hello")

            thr = MyThread()
            thr.start()
            thr.join()
            """)
        out = self.run_command("coverage run --timid bug164.py")

        self.assertIn("Hello\n", out)
        self.assertNotIn("warning", out)

    def test_warning_trace_function_changed(self):
        self.make_file("settrace.py", """\
            import sys
            print("Hello")
            sys.settrace(None)
            print("Goodbye")
            """)
        out = self.run_command("coverage run --timid settrace.py")
        self.assertIn("Hello\n", out)
        self.assertIn("Goodbye\n", out)

        self.assertIn("Trace function changed", out)

    def test_fullcoverage(self):                        # pragma: not covered
        if env.PY2:             # This doesn't work on Python 2.
            self.skip("fullcoverage doesn't work on Python 2.")
        # It only works with the C tracer, and if we aren't measuring ourselves.
        if not env.C_TRACER or env.METACOV:
            self.skip("fullcoverage only works with the C tracer.")

        # fullcoverage is a trick to get stdlib modules measured from
        # the very beginning of the process. Here we import os and
        # then check how many lines are measured.
        self.make_file("getenv.py", """\
            import os
            print("FOOEY == %s" % os.getenv("FOOEY"))
            """)

        fullcov = os.path.join(
            os.path.dirname(coverage.__file__), "fullcoverage"
            )
        self.set_environ("FOOEY", "BOO")
        self.set_environ("PYTHONPATH", fullcov)
        out = self.run_command("python -m coverage run -L getenv.py")
        self.assertEqual(out, "FOOEY == BOO\n")
        data = coverage.CoverageData()
        data.read_file(".coverage")
        # The actual number of executed lines in os.py when it's
        # imported is 120 or so.  Just running os.getenv executes
        # about 5.
        self.assertGreater(data.summary()['os.py'], 50)

    def test_deprecation_warnings(self):
        # Test that coverage doesn't trigger deprecation warnings.
        # https://bitbucket.org/ned/coveragepy/issue/305/pendingdeprecationwarning-the-imp-module
        self.make_file("allok.py", """\
            import warnings
            warnings.simplefilter('default')
            import coverage
            print("No warnings!")
            """)
        out = self.run_command("python allok.py")
        self.assertEqual(out, "No warnings!\n")

    def test_run_twice(self):
        # https://bitbucket.org/ned/coveragepy/issue/353/40a3-introduces-an-unexpected-third-case
        self.make_file("foo.py", """\
            def foo():
                pass
            """)
        self.make_file("run_twice.py", """\
            import coverage

            for _ in [1, 2]:
                inst = coverage.Coverage(source=['foo'])
                inst.load()
                inst.start()
                import foo
                inst.stop()
                inst.combine()
                inst.save()
            """)
        out = self.run_command("python run_twice.py")
        self.assertEqual(
            out,
            "Coverage.py warning: "
            "Module foo was previously imported, but not measured.\n"
        )


class AliasedCommandTest(CoverageTest):
    """Tests of the version-specific command aliases."""

    run_in_temp_dir = False

    def test_major_version_works(self):
        # "coverage2" works on py2
        cmd = "coverage%d" % sys.version_info[0]
        out = self.run_command(cmd)
        self.assertIn("Code coverage for Python", out)

    def test_wrong_alias_doesnt_work(self):
        # "coverage3" doesn't work on py2
        badcmd = "coverage%d" % (5 - sys.version_info[0])
        out = self.run_command(badcmd)
        self.assertNotIn("Code coverage for Python", out)

    def test_specific_alias_works(self):
        # "coverage-2.7" works on py2.7
        cmd = "coverage-%d.%d" % sys.version_info[:2]
        out = self.run_command(cmd)
        self.assertIn("Code coverage for Python", out)


class PydocTest(CoverageTest):
    """Test that pydoc can get our information."""

    run_in_temp_dir = False

    def assert_pydoc_ok(self, name, thing):
        """Check that pydoc of `name` finds the docstring from `thing`."""
        # Run pydoc.
        out = self.run_command("python -m pydoc " + name)
        # It should say "Help on..", and not have a traceback
        self.assert_starts_with(out, "Help on ")
        self.assertNotIn("Traceback", out)

        # All of the lines in the docstring should be there somewhere.
        for line in thing.__doc__.splitlines():
            self.assertIn(line.strip(), out)

    def test_pydoc_coverage(self):
        self.assert_pydoc_ok("coverage", coverage)

    def test_pydoc_coverage_coverage(self):
        self.assert_pydoc_ok("coverage.Coverage", coverage.Coverage)


class FailUnderTest(CoverageTest):
    """Tests of the --fail-under switch."""

    def setUp(self):
        super(FailUnderTest, self).setUp()
        self.make_file("forty_two_plus.py", """\
            # I have 42.857% (3/7) coverage!
            a = 1
            b = 2
            if a > 3:
                b = 4
                c = 5
                d = 6
                e = 7
            """)
        st, _ = self.run_command_status("coverage run forty_two_plus.py")
        self.assertEqual(st, 0)
        st, out = self.run_command_status("coverage report")
        self.assertEqual(st, 0)
        self.assertEqual(
            self.last_line_squeezed(out),
            "forty_two_plus.py 7 4 43%"
        )

    def test_report(self):
        st, _ = self.run_command_status("coverage report --fail-under=42")
        self.assertEqual(st, 0)
        st, _ = self.run_command_status("coverage report --fail-under=43")
        self.assertEqual(st, 0)
        st, _ = self.run_command_status("coverage report --fail-under=44")
        self.assertEqual(st, 2)

    def test_html_report(self):
        st, _ = self.run_command_status("coverage html --fail-under=42")
        self.assertEqual(st, 0)
        st, _ = self.run_command_status("coverage html --fail-under=43")
        self.assertEqual(st, 0)
        st, _ = self.run_command_status("coverage html --fail-under=44")
        self.assertEqual(st, 2)

    def test_xml_report(self):
        st, _ = self.run_command_status("coverage xml --fail-under=42")
        self.assertEqual(st, 0)
        st, _ = self.run_command_status("coverage xml --fail-under=43")
        self.assertEqual(st, 0)
        st, _ = self.run_command_status("coverage xml --fail-under=44")
        self.assertEqual(st, 2)

    def test_fail_under_in_config(self):
        self.make_file(".coveragerc", "[report]\nfail_under = 43\n")
        st, _ = self.run_command_status("coverage report")
        self.assertEqual(st, 0)

        self.make_file(".coveragerc", "[report]\nfail_under = 44\n")
        st, _ = self.run_command_status("coverage report")
        self.assertEqual(st, 2)


class FailUnderNoFilesTest(CoverageTest):
    def setUp(self):
        super(FailUnderNoFilesTest, self).setUp()
        self.make_file(".coveragerc", "[report]\nfail_under = 99\n")

    def test_report(self):
        st, out = self.run_command_status("coverage report")
        self.assertIn('No data to report.', out)
        self.assertEqual(st, 1)

    def test_xml(self):
        st, out = self.run_command_status("coverage xml")
        self.assertIn('No data to report.', out)
        self.assertEqual(st, 1)

    def test_html(self):
        st, out = self.run_command_status("coverage html")
        self.assertIn('No data to report.', out)
        self.assertEqual(st, 1)


class FailUnderEmptyFilesTest(CoverageTest):
    def setUp(self):
        super(FailUnderEmptyFilesTest, self).setUp()

        self.make_file(".coveragerc", "[report]\nfail_under = 99\n")
        self.make_file("empty.py", "")
        st, _ = self.run_command_status("coverage run empty.py")
        self.assertEqual(st, 0)

    def test_report(self):
        st, _ = self.run_command_status("coverage report")
        self.assertEqual(st, 2)

    def test_xml(self):
        st, _ = self.run_command_status("coverage xml")
        self.assertEqual(st, 2)

    def test_html(self):
        st, _ = self.run_command_status("coverage html")
        self.assertEqual(st, 2)


def possible_pth_dirs():
    """Produce a sequence of directories for trying to write .pth files."""
    # First look through sys.path, and we find a .pth file, then it's a good
    # place to put ours.
    for d in sys.path:
        g = glob.glob(os.path.join(d, "*.pth"))
        if g:
            yield d

    # If we're still looking, then try the Python library directory.
    # https://bitbucket.org/ned/coveragepy/issue/339/pth-test-malfunctions
    import distutils.sysconfig
    yield distutils.sysconfig.get_python_lib()


class ProcessCoverageMixin(object):
    """Set up a .pth file that causes all sub-processes to be coverage'd"""

    def setUp(self):
        super(ProcessCoverageMixin, self).setUp()
        # Find a place to put a .pth file.
        pth_contents = "import coverage; coverage.process_startup()\n"
        for pth_dir in possible_pth_dirs():             # pragma: part covered
            pth_path = os.path.join(pth_dir, "subcover.pth")
            with open(pth_path, "w") as pth:
                try:
                    pth.write(pth_contents)
                    self.pth_path = pth_path
                    break
                except (IOError, OSError):              # pragma: not covered
                    pass
        else:                                           # pragma: not covered
            raise Exception("Couldn't find a place for the .pth file")

        self.addCleanup(os.remove, self.pth_path)


class ProcessStartupTest(ProcessCoverageMixin, CoverageTest):
    """Test that we can measure coverage in sub-processes."""

    def test_subprocess_with_pth_files(self):           # pragma: not covered
        if env.METACOV:
            self.skip(
                "Can't test sub-process pth file suppport during metacoverage"
                )

        # Main will run sub.py
        self.make_file("main.py", """\
            import os, os.path, sys
            ex = os.path.basename(sys.executable)
            os.system(ex + " sub.py")
            """)
        # sub.py will write a few lines.
        self.make_file("sub.py", """\
            with open("out.txt", "w") as f:
                f.write("Hello, world!\\n")
            """)
        self.make_file("coverage.ini", """\
            [run]
            data_file = .mycovdata
            """)
        self.set_environ("COVERAGE_PROCESS_START", "coverage.ini")
        import main             # pylint: disable=import-error,unused-variable

        with open("out.txt") as f:
            self.assertEqual(f.read(), "Hello, world!\n")

        # Read the data from .coverage
        self.assert_exists(".mycovdata")
        data = coverage.CoverageData()
        data.read_file(".mycovdata")
        self.assertEqual(data.summary()['sub.py'], 2)


class ProcessStartupWithSourceTest(ProcessCoverageMixin, CoverageTest):
    """Show that we can configure {[run]source} during process-level coverage.

    There are three interesting variables, for a total of eight tests:

        1. -m versus a simple script argument (for example, `python myscript`),

        2. filtering for the top-level (main.py) or second-level (sub.py)
           module, and

        3. whether the files are in a package or not.

    """

    def assert_pth_and_source_work_together(
        self, dashm, package, source
    ):                                                  # pragma: not covered
        if env.METACOV:
            self.skip(
                "Can't test sub-process pth file suppport during metacoverage"
                )

        def fullname(modname):
            if package and dashm:
                return '.'.join((package, modname))
            else:
                return modname

        def path(basename):
            return os.path.join(package, basename)

        # Main will run sub.py.
        self.make_file(path("main.py"), """\
            import %s
            if True: pass
            """ % fullname('sub'))
        if package:
            self.make_file(path("__init__.py"), "")
        # sub.py will write a few lines.
        self.make_file(path("sub.py"), """\
            with open("out.txt", "w") as f:
                f.write("Hello, world!")
            """)
        self.make_file("coverage.ini", """\
            [run]
            source = %s
            """ % fullname(source))

        self.set_environ("COVERAGE_PROCESS_START", "coverage.ini")

        if dashm:
            cmd = (sys.executable, dashm, fullname('main'))
        else:
            cmd = (sys.executable, path('main.py'))

        # TODO: can we use run_command here instead of Popen?
        from subprocess import Popen
        Popen(cmd).wait()

        with open("out.txt") as f:
            self.assertEqual(f.read(), "Hello, world!")

        # Read the data from .coverage
        self.assert_exists(".coverage")
        data = coverage.CoverageData()
        data.read_file(".coverage")
        summary = data.summary()
        print(summary)
        self.assertEqual(summary[source + '.py'], 2)
        self.assertEqual(len(summary), 1)

    def test_dashm_main(self):
        self.assert_pth_and_source_work_together('-m', '', 'main')

    def test_script_main(self):
        self.assert_pth_and_source_work_together('', '', 'main')

    def test_dashm_sub(self):
        self.assert_pth_and_source_work_together('-m', '', 'sub')

    def test_script_sub(self):
        self.assert_pth_and_source_work_together('', '', 'sub')

    def test_dashm_pkg_main(self):
        self.assert_pth_and_source_work_together('-m', 'pkg', 'main')

    def test_script_pkg_main(self):
        self.assert_pth_and_source_work_together('', 'pkg', 'main')

    def test_dashm_pkg_sub(self):
        self.assert_pth_and_source_work_together('-m', 'pkg', 'sub')

    def test_script_pkg_sub(self):
        self.assert_pth_and_source_work_together('', 'pkg', 'sub')
