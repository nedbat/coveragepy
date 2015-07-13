"""Tests for concurrency libraries."""

import os
import os.path
import threading

import coverage
from coverage import env

from tests.coveragetest import CoverageTest


# These libraries aren't always available, we'll skip tests if they aren't.

try:
    import eventlet
except ImportError:
    eventlet = None

try:
    import gevent
except ImportError:
    gevent = None

try:
    import greenlet
except ImportError:
    greenlet = None


def line_count(s):
    """How many non-blank non-comment lines are in `s`?"""
    def code_line(l):
        """Is this a code line? Not blank, and not a full-line comment."""
        return l.strip() and not l.strip().startswith('#')
    return sum(1 for l in s.splitlines() if code_line(l))


class ConcurrencyTest(CoverageTest):
    """Tests of the concurrency support in coverage.py."""

    LIMIT = 1000

    # The code common to all the concurrency models.
    COMMON = """
        class Producer(threading.Thread):
            def __init__(self, q):
                threading.Thread.__init__(self)
                self.q = q

            def run(self):
                for i in range({LIMIT}):
                    self.q.put(i)
                self.q.put(None)

        class Consumer(threading.Thread):
            def __init__(self, q):
                threading.Thread.__init__(self)
                self.q = q

            def run(self):
                sum = 0
                while True:
                    i = self.q.get()
                    if i is None:
                        print(sum)
                        break
                    sum += i

        q = queue.Queue()
        c = Consumer(q)
        p = Producer(q)
        c.start()
        p.start()

        p.join()
        c.join()
        """.format(LIMIT=LIMIT)

    # Import the things to use threads.
    if env.PY2:
        THREAD = """\
        import threading
        import Queue as queue
        """ + COMMON
    else:
        THREAD = """\
        import threading
        import queue
        """ + COMMON

    # Import the things to use eventlet.
    EVENTLET = """\
        import eventlet.green.threading as threading
        import eventlet.queue as queue
        """ + COMMON

    # Import the things to use gevent.
    GEVENT = """\
        from gevent import monkey
        monkey.patch_thread()
        import threading
        import gevent.queue as queue
        """ + COMMON

    # Uncomplicated code that doesn't use any of the concurrency stuff, to test
    # the simple case under each of the regimes.
    SIMPLE = """\
        total = 0
        for i in range({LIMIT}):
            total += i
        print(total)
        """.format(LIMIT=LIMIT)

    def try_some_code(self, code, concurrency, the_module, expected_out=None):
        """Run some concurrency testing code and see that it was all covered.

        `code` is the Python code to execute.  `concurrency` is the name of
        the concurrency regime to test it under.  `the_module` is the imported
        module that must be available for this to work at all. `expected_out`
        is the text we expect the code to produce.

        """

        self.make_file("try_it.py", code)

        cmd = "coverage run --concurrency=%s try_it.py" % concurrency
        out = self.run_command(cmd)

        if not the_module:
            # We don't even have the underlying module installed, we expect
            # coverage to alert us to this fact.
            expected_out = (
                "Couldn't trace with concurrency=%s, "
                "the module isn't installed.\n" % concurrency
            )
            self.assertEqual(out, expected_out)
        elif env.C_TRACER or concurrency == "thread":
            # We can fully measure the code if we are using the C tracer, which
            # can support all the concurrency, or if we are using threads.
            if expected_out is None:
                expected_out = "%d\n" % (sum(range(self.LIMIT)))
            self.assertEqual(out, expected_out)

            # Read the coverage file and see that try_it.py has all its lines
            # executed.
            data = coverage.CoverageData()
            data.read_file(".coverage")

            # If the test fails, it's helpful to see this info:
            fname = os.path.abspath("try_it.py")
            linenos = data.line_data(fname)
            print("{0}: {1}".format(len(linenos), linenos))
            print_simple_annotation(code, linenos)

            lines = line_count(code)
            self.assertEqual(data.summary()['try_it.py'], lines)
        else:
            expected_out = (
                "Can't support concurrency=%s with PyTracer, "
                "only threads are supported\n" % concurrency
            )
            self.assertEqual(out, expected_out)

    def test_threads(self):
        self.try_some_code(self.THREAD, "thread", threading)

    def test_threads_simple_code(self):
        self.try_some_code(self.SIMPLE, "thread", threading)

    def test_eventlet(self):
        self.try_some_code(self.EVENTLET, "eventlet", eventlet)

    def test_eventlet_simple_code(self):
        self.try_some_code(self.SIMPLE, "eventlet", eventlet)

    def test_gevent(self):
        self.try_some_code(self.GEVENT, "gevent", gevent)

    def test_gevent_simple_code(self):
        self.try_some_code(self.SIMPLE, "gevent", gevent)

    def test_greenlet(self):
        GREENLET = """\
            from greenlet import greenlet

            def test1(x, y):
                z = gr2.switch(x+y)
                print(z)

            def test2(u):
                print(u)
                gr1.switch(42)

            gr1 = greenlet(test1)
            gr2 = greenlet(test2)
            gr1.switch("hello", " world")
            """
        self.try_some_code(GREENLET, "greenlet", greenlet, "hello world\n42\n")

    def test_greenlet_simple_code(self):
        self.try_some_code(self.SIMPLE, "greenlet", greenlet)

    def test_bug_330(self):
        BUG_330 = """\
            from weakref import WeakKeyDictionary
            import eventlet

            def do():
                eventlet.sleep(.01)

            gts = WeakKeyDictionary()
            for _ in range(100):
                gts[eventlet.spawn(do)] = True
                eventlet.sleep(.005)

            eventlet.sleep(.1)
            print len(gts)
            """
        self.try_some_code(BUG_330, "eventlet", eventlet, "0\n")


class MultiprocessingTest(CoverageTest):
    """Test support of the multiprocessing module."""

    def setUp(self):
        super(MultiprocessingTest, self).setUp()
        # Currently, this doesn't work on Windows, something about pickling
        # the monkey-patched Process class?
        if env.WINDOWS:
            self.skip("Multiprocessing support doesn't work on Windows")

    def test_multiprocessing(self):
        self.make_file("multi.py", """\
            import multiprocessing
            import os
            import time

            def func(x):
                # Need to pause, or the tasks go too quick, and some processes
                # in the pool don't get any work, and then don't record data.
                time.sleep(0.02)
                # Use different lines in different subprocesses.
                if x % 2:
                    y = x*x
                else:
                    y = x*x*x
                return os.getpid(), y

            if __name__ == "__main__":
                pool = multiprocessing.Pool(3)
                inputs = range(30)
                outputs = pool.imap_unordered(func, inputs)
                pids = set()
                total = 0
                for pid, sq in outputs:
                    pids.add(pid)
                    total += sq
                print("%d pids, total = %d" % (len(pids), total))
                pool.close()
                pool.join()
            """)

        out = self.run_command(
            "coverage run --concurrency=multiprocessing multi.py"
        )
        total = sum(x*x if x%2 else x*x*x for x in range(30))
        self.assertEqual(out.rstrip(), "3 pids, total = %d" % total)

        self.run_command("coverage combine")
        out = self.run_command("coverage report -m")
        last_line = self.squeezed_lines(out)[-1]
        self.assertEqual(last_line, "multi.py 21 0 100%")


def print_simple_annotation(code, linenos):
    """Print the lines in `code` with X for each line number in `linenos`."""
    for lineno, line in enumerate(code.splitlines(), start=1):
        print(" {0} {1}".format("X" if lineno in linenos else " ", line))
