# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Oddball cases for testing coverage.py"""

import os.path
import re
import sys

from flaky import flaky
import pytest

import coverage
from coverage import env
from coverage.files import abs_file
from coverage.misc import import_local_file

from tests.coveragetest import CoverageTest
from tests.helpers import swallow_warnings
from tests import osinfo


class ThreadingTest(CoverageTest):
    """Tests of the threading support."""

    def test_threading(self):
        self.check_coverage("""\
            import threading

            def fromMainThread():
                return "called from main thread"

            def fromOtherThread():
                return "called from other thread"

            def neverCalled():
                return "no one calls me"

            other = threading.Thread(target=fromOtherThread)
            other.start()
            fromMainThread()
            other.join()
            """,
            [1, 3, 4, 6, 7, 9, 10, 12, 13, 14, 15], "10")

    def test_thread_run(self):
        self.check_coverage("""\
            import threading

            class TestThread(threading.Thread):
                def run(self):
                    self.a = 5
                    self.do_work()
                    self.a = 7

                def do_work(self):
                    self.a = 10

            thd = TestThread()
            thd.start()
            thd.join()
            """,
            [1, 3, 4, 5, 6, 7, 9, 10, 12, 13, 14], "")


class RecursionTest(CoverageTest):
    """Check what happens when recursive code gets near limits."""

    def test_short_recursion(self):
        # We can definitely get close to 500 stack frames.
        self.check_coverage("""\
            def recur(n):
                if n == 0:
                    return 0
                else:
                    return recur(n-1)+1

            recur(495)  # We can get at least this many stack frames.
            i = 8       # and this line will be traced
            """,
            [1, 2, 3, 5, 7, 8], "")

    def test_long_recursion(self):
        # We can't finish a very deep recursion, but we don't crash.
        with pytest.raises(RuntimeError):
            with swallow_warnings("Trace function changed, data is likely wrong: None"):
                self.check_coverage("""\
                    def recur(n):
                        if n == 0:
                            return 0
                        else:
                            return recur(n-1)+1

                    recur(100000)  # This is definitely too many frames.
                    """,
                    [1, 2, 3, 5, 7], ""
                )

    def test_long_recursion_recovery(self):
        # Test the core of bug 93: https://github.com/nedbat/coveragepy/issues/93
        # When recovering from a stack overflow, the Python trace function is
        # disabled, but the C trace function is not.  So if we're using a
        # Python trace function, we won't trace anything after the stack
        # overflow, and there should be a warning about it.  If we're using
        # the C trace function, only line 3 will be missing, and all else
        # will be traced.

        self.make_file("recur.py", """\
            def recur(n):
                if n == 0:
                    return 0    # never hit
                else:
                    return recur(n-1)+1

            try:
                recur(100000)  # This is definitely too many frames.
            except RuntimeError:
                i = 10
            i = 11
            """)

        cov = coverage.Coverage()
        with swallow_warnings("Trace function changed, data is likely wrong: None"):
            self.start_import_stop(cov, "recur")

        pytrace = (cov._collector.tracer_name() == "PyTracer")
        expected_missing = [3]
        if pytrace:                                 # pragma: no metacov
            expected_missing += [9, 10, 11]

        _, statements, missing, _ = cov.analysis("recur.py")
        assert statements == [1, 2, 3, 5, 7, 8, 9, 10, 11]
        assert expected_missing == missing

        # Get a warning about the stackoverflow effect on the tracing function.
        if pytrace:                                 # pragma: no metacov
            assert len(cov._warnings) == 1
            assert re.fullmatch(
                r"Trace function changed, data is likely wrong: None != " +
                r"<bound method PyTracer._trace of " +
                "<PyTracer at 0x[0-9a-fA-F]+: 5 lines in 1 files>>",
                cov._warnings[0],
            )
        else:
            assert not cov._warnings


class MemoryLeakTest(CoverageTest):
    """Attempt the impossible: test that memory doesn't leak.

    Note: this test is truly unusual, and has had a colorful history.  See
    for example: https://github.com/nedbat/coveragepy/issues/186

    It may still fail occasionally, especially on PyPy.

    """
    @flaky
    @pytest.mark.skipif(env.JYTHON, reason="Don't bother on Jython")
    @pytest.mark.skipif(not env.C_TRACER, reason="Only the C tracer has refcounting issues")
    def test_for_leaks(self):
        # Our original bad memory leak only happened on line numbers > 255, so
        # make a code object with more lines than that.  Ugly string mumbo
        # jumbo to get 300 blank lines at the beginning..
        code = """\
            # blank line\n""" * 300 + """\
            def once(x):                                        # line 301
                if x % 100 == 0:
                    raise Exception("100!")
                elif x % 2:
                    return 10
                else:                                           # line 306
                    return 11
            i = 0 # Portable loop without alloc'ing memory.
            while i < ITERS:
                try:
                    once(i)
                except:
                    pass
                i += 1                                          # line 315
            """
        lines = list(range(301, 315))
        lines.remove(306)       # Line 306 is the "else".

        # This is a non-deterministic test, so try it a few times, and fail it
        # only if it predominantly fails.
        fails = 0
        for _ in range(10):
            ram_0 = osinfo.process_ram()
            self.check_coverage(code.replace("ITERS", "10"), lines, "")
            ram_10 = osinfo.process_ram()
            self.check_coverage(code.replace("ITERS", "10000"), lines, "")
            ram_10k = osinfo.process_ram()
            # Running the code 10k times shouldn't grow the ram much more than
            # running it 10 times.
            ram_growth = (ram_10k - ram_10) - (ram_10 - ram_0)
            if ram_growth > 100000:
                fails += 1                                  # pragma: only failure

        if fails > 8:
            pytest.fail("RAM grew by %d" % (ram_growth))      # pragma: only failure


class MemoryFumblingTest(CoverageTest):
    """Test that we properly manage the None refcount."""

    @pytest.mark.skipif(not env.C_TRACER, reason="Only the C tracer has refcounting issues")
    def test_dropping_none(self):                           # pragma: not covered
        # TODO: Mark this so it will only be run sometimes.
        pytest.skip("This is too expensive for now (30s)")
        # Start and stop coverage thousands of times to flush out bad
        # reference counting, maybe.
        self.make_file("the_code.py", """\
            import random
            def f():
                if random.random() > .5:
                    x = 1
                else:
                    x = 2
            """)
        self.make_file("main.py", """\
            import coverage
            import sys
            from the_code import f
            for i in range(10000):
                cov = coverage.Coverage(branch=True)
                cov.start()
                f()
                cov.stop()
                cov.erase()
            print("Final None refcount: %d" % (sys.getrefcount(None)))
            """)
        status, out = self.run_command_status("python main.py")
        assert status == 0
        assert "Final None refcount" in out
        assert "Fatal" not in out


@pytest.mark.skipif(env.JYTHON, reason="Pyexpat isn't a problem on Jython")
class PyexpatTest(CoverageTest):
    """Pyexpat screws up tracing. Make sure we've counter-defended properly."""

    def test_pyexpat(self):
        # pyexpat calls the trace function explicitly (inexplicably), and does
        # it wrong for exceptions.  Parsing a DOCTYPE for some reason throws
        # an exception internally, and triggers its wrong behavior.  This test
        # checks that our fake PyTrace_RETURN hack in tracer.c works.  It will
        # also detect if the pyexpat bug is fixed unbeknownst to us, meaning
        # we'd see two RETURNs where there should only be one.

        self.make_file("trydom.py", """\
            import xml.dom.minidom

            XML = '''\\
            <!DOCTYPE fooey SYSTEM "http://www.example.com/example.dtd">
            <root><child/><child/></root>
            '''

            def foo():
                dom = xml.dom.minidom.parseString(XML)
                assert len(dom.getElementsByTagName('child')) == 2
                a = 11

            foo()
            """)

        self.make_file("outer.py", "\n"*100 + "import trydom\na = 102\n")

        cov = coverage.Coverage()
        cov.erase()

        # Import the Python file, executing it.
        self.start_import_stop(cov, "outer")

        _, statements, missing, _ = cov.analysis("trydom.py")
        assert statements == [1, 3, 8, 9, 10, 11, 13]
        assert missing == []

        _, statements, missing, _ = cov.analysis("outer.py")
        assert statements == [101, 102]
        assert missing == []

        # Make sure pyexpat isn't recorded as a source file.
        # https://github.com/nedbat/coveragepy/issues/419
        files = cov.get_data().measured_files()
        msg = f"Pyexpat.c is in the measured files!: {files!r}:"
        assert not any(f.endswith("pyexpat.c") for f in files), msg


class ExceptionTest(CoverageTest):
    """I suspect different versions of Python deal with exceptions differently
    in the trace function.
    """

    def test_exception(self):
        # Python 2.3's trace function doesn't get called with "return" if the
        # scope is exiting due to an exception.  This confounds our trace
        # function which relies on scope announcements to track which files to
        # trace.
        #
        # This test is designed to sniff this out.  Each function in the call
        # stack is in a different file, to try to trip up the tracer.  Each
        # file has active lines in a different range so we'll see if the lines
        # get attributed to the wrong file.

        self.make_file("oops.py", """\
            def oops(args):
                a = 2
                raise Exception("oops")
                a = 4
            """)

        self.make_file("fly.py", "\n"*100 + """\
            def fly(calls):
                a = 2
                calls[0](calls[1:])
                a = 4
            """)

        self.make_file("catch.py", "\n"*200 + """\
            def catch(calls):
                try:
                    a = 3
                    calls[0](calls[1:])
                    a = 5
                except:
                    a = 7
            """)

        self.make_file("doit.py", "\n"*300 + """\
            def doit(calls):
                try:
                    calls[0](calls[1:])
                except:
                    a = 5
            """)

        # Import all the modules before starting coverage, so the def lines
        # won't be in all the results.
        for mod in "oops fly catch doit".split():
            import_local_file(mod)

        # Each run nests the functions differently to get different
        # combinations of catching exceptions and letting them fly.
        runs = [
            ("doit fly oops", {
                'doit.py': [302, 303, 304, 305],
                'fly.py': [102, 103],
                'oops.py': [2, 3],
            }),
            ("doit catch oops", {
                'doit.py': [302, 303],
                'catch.py': [202, 203, 204, 206, 207],
                'oops.py': [2, 3],
            }),
            ("doit fly catch oops", {
                'doit.py': [302, 303],
                'fly.py': [102, 103, 104],
                'catch.py': [202, 203, 204, 206, 207],
                'oops.py': [2, 3],
            }),
            ("doit catch fly oops", {
                'doit.py': [302, 303],
                'catch.py': [202, 203, 204, 206, 207],
                'fly.py': [102, 103],
                'oops.py': [2, 3],
            }),
        ]

        for callnames, lines_expected in runs:

            # Make the list of functions we'll call for this test.
            callnames = callnames.split()
            calls = [getattr(sys.modules[cn], cn) for cn in callnames]

            cov = coverage.Coverage()
            cov.start()
            # Call our list of functions: invoke the first, with the rest as
            # an argument.
            calls[0](calls[1:])     # pragma: nested
            cov.stop()              # pragma: nested

            # Clean the line data and compare to expected results.
            # The file names are absolute, so keep just the base.
            clean_lines = {}
            data = cov.get_data()
            for callname in callnames:
                filename = callname + ".py"
                lines = data.lines(abs_file(filename))
                clean_lines[filename] = sorted(lines)

            if env.JYTHON:                  # pragma: only jython
                # Jython doesn't report on try or except lines, so take those
                # out of the expected lines.
                invisible = [202, 206, 302, 304]
                for lines in lines_expected.values():
                    lines[:] = [l for l in lines if l not in invisible]

            assert clean_lines == lines_expected


class DoctestTest(CoverageTest):
    """Tests invoked with doctest should measure properly."""

    def test_doctest(self):
        # Doctests used to be traced, with their line numbers credited to the
        # file they were in.  Below, one of the doctests has four lines (1-4),
        # which would incorrectly claim that lines 1-4 of the file were
        # executed.  In this file, line 2 is not executed.
        self.make_file("the_doctest.py", '''\
            if "x" in "abc":
                print("hello")
            def return_arg_or_void(arg):
                """If <arg> is None, return "Void"; otherwise return <arg>

                >>> return_arg_or_void(None)
                'Void'
                >>> return_arg_or_void("arg")
                'arg'
                >>> return_arg_or_void("None")
                'None'
                >>> if "x" in "xyz":                # line 1
                ...   if "a" in "aswed":            # line 2
                ...      if "a" in "abc":           # line 3
                ...         return_arg_or_void(12)  # line 4
                12
                """
                if arg is None:
                    return "Void"
                else:
                    return arg

            import doctest, sys
            doctest.testmod(sys.modules[__name__])  # we're not __main__ :(
            ''')
        cov = coverage.Coverage()
        self.start_import_stop(cov, "the_doctest")
        data = cov.get_data()
        assert len(data.measured_files()) == 1
        lines = data.lines(data.measured_files().pop())
        assert lines == [1, 3, 18, 19, 21, 23, 24]


class GettraceTest(CoverageTest):
    """Tests that we work properly with `sys.gettrace()`."""
    def test_round_trip_in_untraced_function(self):
        # https://github.com/nedbat/coveragepy/issues/575
        self.make_file("main.py", """import sample""")
        self.make_file("sample.py", """\
            from swap import swap_it
            def doit():
                print(3)
                swap_it()
                print(5)
            def doit_soon():
                print(7)
                doit()
                print(9)
            print(10)
            doit_soon()
            print(12)
            """)
        self.make_file("swap.py", """\
            import sys
            def swap_it():
                sys.settrace(sys.gettrace())
            """)

        # Use --source=sample to prevent measurement of swap.py.
        cov = coverage.Coverage(source=["sample"])
        self.start_import_stop(cov, "main")

        assert self.stdout() == "10\n7\n3\n5\n9\n12\n"

        _, statements, missing, _ = cov.analysis("sample.py")
        assert statements == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        assert missing == []

    def test_setting_new_trace_function(self):
        # https://github.com/nedbat/coveragepy/issues/436
        self.check_coverage('''\
            import os.path
            import sys

            def tracer(frame, event, arg):
                filename = os.path.basename(frame.f_code.co_filename)
                print(f"{event}: {filename} @ {frame.f_lineno}")
                return tracer

            def begin():
                sys.settrace(tracer)

            def collect():
                t = sys.gettrace()
                assert t is tracer, t

            def test_unsets_trace():
                begin()
                collect()

            old = sys.gettrace()
            test_unsets_trace()
            sys.settrace(old)
            a = 21
            b = 22
            ''',
            lines=[1, 2, 4, 5, 6, 7, 9, 10, 12, 13, 14, 16, 17, 18, 20, 21, 22, 23, 24],
            missing="5-7, 13-14",
        )

        out = self.stdout().replace(self.last_module_name, "coverage_test")
        expected = (
            "call: coverage_test.py @ 12\n" +
            "line: coverage_test.py @ 13\n" +
            "line: coverage_test.py @ 14\n" +
            "return: coverage_test.py @ 14\n"
        )
        assert expected == out

    @pytest.mark.expensive
    @pytest.mark.skipif(env.METACOV, reason="Can't set trace functions during meta-coverage")
    def test_atexit_gettrace(self):
        # This is not a test of coverage at all, but of our understanding
        # of this edge-case behavior in various Pythons.

        self.make_file("atexit_gettrace.py", """\
            import atexit, sys

            def trace_function(frame, event, arg):
                return trace_function
            sys.settrace(trace_function)

            def show_trace_function():
                tfn = sys.gettrace()
                if tfn is not None:
                    tfn = tfn.__name__
                print(tfn)
            atexit.register(show_trace_function)

            # This will show what the trace function is at the end of the program.
            """)
        status, out = self.run_command_status("python atexit_gettrace.py")
        assert status == 0
        if env.PYPY and env.PYPYVERSION >= (5, 4):
            # Newer PyPy clears the trace function before atexit runs.
            assert out == "None\n"
        else:
            # Other Pythons leave the trace function in place.
            assert out == "trace_function\n"


class ExecTest(CoverageTest):
    """Tests of exec."""
    def test_correct_filename(self):
        # https://github.com/nedbat/coveragepy/issues/380
        # Bug was that exec'd files would have their lines attributed to the
        # calling file.  Make two files, both with ~30 lines, but no lines in
        # common.  Line 30 in to_exec.py was recorded as line 30 in main.py,
        # but now it's fixed. :)
        self.make_file("to_exec.py", """\
            \n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n
            print("var is {}".format(var))         # line 31
            """)
        self.make_file("main.py", """\
            namespace = {'var': 17}
            with open("to_exec.py") as to_exec_py:
                code = compile(to_exec_py.read(), 'to_exec.py', 'exec')
                exec(code, globals(), namespace)
            \n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n
            print("done")                           # line 35
            """)

        cov = coverage.Coverage()
        self.start_import_stop(cov, "main")

        _, statements, missing, _ = cov.analysis("main.py")
        assert statements == [1, 2, 3, 4, 35]
        assert missing == []
        _, statements, missing, _ = cov.analysis("to_exec.py")
        assert statements == [31]
        assert missing == []

    def test_unencodable_filename(self):
        # https://github.com/nedbat/coveragepy/issues/891
        self.make_file("bug891.py", r"""exec(compile("pass", "\udcff.py", "exec"))""")
        cov = coverage.Coverage()
        self.start_import_stop(cov, "bug891")
        # Saving would fail trying to encode \udcff.py
        cov.save()
        files = [os.path.basename(f) for f in cov.get_data().measured_files()]
        assert "bug891.py" in files


class MockingProtectionTest(CoverageTest):
    """Tests about protecting ourselves from aggressive mocking.

    https://github.com/nedbat/coveragepy/issues/416

    """
    def test_os_path_exists(self):
        # To see if this test still detects the problem, change isolate_module
        # in misc.py to simply return its argument.  It should fail with a
        # StopIteration error.
        self.make_file("bug416.py", """\
            import os.path
            from unittest import mock

            @mock.patch('os.path.exists')
            def test_path_exists(mock_exists):
                mock_exists.side_effect = [17]
                print("in test")
                import bug416a
                print(bug416a.foo)
                print(os.path.exists("."))

            test_path_exists()
            """)
        self.make_file("bug416a.py", """\
            print("bug416a.py")
            foo = 23
            """)

        import py_compile
        py_compile.compile("bug416a.py")
        out = self.run_command("coverage run bug416.py")
        assert out == "in test\nbug416a.py\n23\n17\n"
