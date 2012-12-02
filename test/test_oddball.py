"""Oddball cases for testing coverage.py"""

import os, sys
import coverage

sys.path.insert(0, os.path.split(__file__)[0]) # Force relative import for Py3k
from coveragetest import CoverageTest
import osinfo

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
            [1,3,4,6,7,9,10,12,13,14,15], "10")

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
            [1,3,4,5,6,7,9,10,12,13,14], "")


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
            [1,2,3,5,7,8], "")

    def test_long_recursion(self):
        # We can't finish a very deep recursion, but we don't crash.
        self.assertRaises(RuntimeError, self.check_coverage,
            """\
            def recur(n):
                if n == 0:
                    return 0
                else:
                    return recur(n-1)+1

            recur(100000)  # This is definitely too many frames.
            """,
            [1,2,3,5,7], "")

    def test_long_recursion_recovery(self):
        # Test the core of bug 93: http://bitbucket.org/ned/coveragepy/issue/93
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

        cov = coverage.coverage()
        self.start_import_stop(cov, "recur")

        pytrace = (cov.collector.tracer_name() == "PyTracer")
        expected_missing = [3]
        if pytrace:
            expected_missing += [9,10,11]

        _, statements, missing, _ = cov.analysis("recur.py")
        self.assertEqual(statements, [1,2,3,5,7,8,9,10,11])
        self.assertEqual(missing, expected_missing)

        # We can get a warning about the stackoverflow effect on the tracing
        # function only if we have sys.gettrace
        if pytrace and hasattr(sys, "gettrace"):
            self.assertEqual(cov._warnings,
                ["Trace function changed, measurement is likely wrong: None"]
                )
        else:
            self.assertEqual(cov._warnings, [])


class MemoryLeakTest(CoverageTest):
    """Attempt the impossible: test that memory doesn't leak.

    Note: this test is truly unusual, and may fail unexpectedly.
    In particular, it is known to fail on PyPy if test_oddball.py is run in
    isolation: https://bitbucket.org/ned/coveragepy/issue/186

    """

    def test_for_leaks(self):
        lines = list(range(301, 315))
        lines.remove(306)
        # Ugly string mumbo jumbo to get 300 blank lines at the beginning..
        code = """\
            # blank line\n""" * 300 + """\
            def once(x):
                if x % 100 == 0:
                    raise Exception("100!")
                elif x % 2:
                    return 10
                else:
                    return 11
            i = 0 # Portable loop without alloc'ing memory.
            while i < ITERS:
                try:
                    once(i)
                except:
                    pass
                i += 1
            """
        ram_0 = osinfo.process_ram()
        self.check_coverage(code.replace("ITERS", "10"), lines, "")
        ram_1 = osinfo.process_ram()
        self.check_coverage(code.replace("ITERS", "10000"), lines, "")
        ram_2 = osinfo.process_ram()
        ram_growth = (ram_2 - ram_1) - (ram_1 - ram_0)
        self.assertTrue(ram_growth < 100000, "RAM grew by %d" % (ram_growth))


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

        cov = coverage.coverage()
        cov.erase()

        # Import the python file, executing it.
        self.start_import_stop(cov, "outer")

        _, statements, missing, _ = cov.analysis("trydom.py")
        self.assertEqual(statements, [1,3,8,9,10,11,13])
        self.assertEqual(missing, [])

        _, statements, missing, _ = cov.analysis("outer.py")
        self.assertEqual(statements, [101,102])
        self.assertEqual(missing, [])


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
            self.import_local_file(mod)

        # Each run nests the functions differently to get different
        # combinations of catching exceptions and letting them fly.
        runs = [
            ("doit fly oops", {
                'doit.py': [302,303,304,305],
                'fly.py': [102,103],
                'oops.py': [2,3],
                }),
            ("doit catch oops", {
                'doit.py': [302,303],
                'catch.py': [202,203,204,206,207],
                'oops.py': [2,3],
                }),
            ("doit fly catch oops", {
                'doit.py': [302,303],
                'fly.py': [102,103,104],
                'catch.py': [202,203,204,206,207],
                'oops.py': [2,3],
                }),
            ("doit catch fly oops", {
                'doit.py': [302,303],
                'catch.py': [202,203,204,206,207],
                'fly.py': [102,103],
                'oops.py': [2,3],
                }),
            ]

        for callnames, lines_expected in runs:

            # Make the list of functions we'll call for this test.
            calls = [getattr(sys.modules[cn], cn) for cn in callnames.split()]

            cov = coverage.coverage()
            cov.start()
            # Call our list of functions: invoke the first, with the rest as
            # an argument.
            calls[0](calls[1:])     # pragma: nested
            cov.stop()              # pragma: nested

            # Clean the line data and compare to expected results.
            # The filenames are absolute, so keep just the base.
            cov._harvest_data() # private! sshhh...
            lines = cov.data.line_data()
            clean_lines = {}
            for f, llist in lines.items():
                if f == __file__:
                    # ignore this file.
                    continue
                clean_lines[os.path.basename(f)] = llist
            self.assertEqual(clean_lines, lines_expected)


if sys.version_info >= (2, 5):
    class DoctestTest(CoverageTest):
        """Tests invoked with doctest should measure properly."""

        def setUp(self):
            super(DoctestTest, self).setUp()

            # Oh, the irony!  This test case exists because Python 2.4's
            # doctest module doesn't play well with coverage.  But nose fixes
            # the problem by monkeypatching doctest.  I want to undo the
            # monkeypatch to be sure I'm getting the doctest module that users
            # of coverage will get.  Deleting the imported module here is
            # enough: when the test imports doctest again, it will get a fresh
            # copy without the monkeypatch.
            del sys.modules['doctest']

        def test_doctest(self):
            self.check_coverage('''\
                def return_arg_or_void(arg):
                    """If <arg> is None, return "Void"; otherwise return <arg>

                    >>> return_arg_or_void(None)
                    'Void'
                    >>> return_arg_or_void("arg")
                    'arg'
                    >>> return_arg_or_void("None")
                    'None'
                    """
                    if arg is None:
                        return "Void"
                    else:
                        return arg

                import doctest, sys
                doctest.testmod(sys.modules[__name__])  # we're not __main__ :(
                ''',
                [1,11,12,14,16,17], "")


if hasattr(sys, 'gettrace'):
    class GettraceTest(CoverageTest):
        """Tests that we work properly with `sys.gettrace()`."""
        def test_round_trip(self):
            self.check_coverage('''\
                import sys
                def foo(n):
                    return 3*n
                def bar(n):
                    return 5*n
                a = foo(6)
                sys.settrace(sys.gettrace())
                a = bar(8)
                ''',
                [1,2,3,4,5,6,7,8], "")

        def test_multi_layers(self):
            self.check_coverage('''\
                import sys
                def level1():
                    a = 3
                    level2()
                    b = 5
                def level2():
                    c = 7
                    sys.settrace(sys.gettrace())
                    d = 9
                e = 10
                level1()
                f = 12
                ''',
                [1,2,3,4,5,6,7,8,9,10,11,12], "")
