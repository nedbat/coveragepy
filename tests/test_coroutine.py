"""Tests for coroutining."""

import os.path, sys

from nose.plugins.skip import SkipTest
import coverage

from tests.coveragetest import CoverageTest


# These libraries aren't always available, we'll skip tests if they aren't.

try:
    import eventlet         # pylint: disable=import-error
except ImportError:
    eventlet = None

try:
    import gevent           # pylint: disable=import-error
except ImportError:
    gevent = None


def line_count(s):
    """How many non-blank non-comment lines are in `s`?"""
    def code_line(l):
        """Is this a code line? Not blank, and not a full-line comment."""
        return l.strip() and not l.strip().startswith('#')
    return sum(1 for l in s.splitlines() if code_line(l))


class CoroutineTest(CoverageTest):
    """Tests of the coroutine support in coverage.py."""

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
    if sys.version_info < (3, 0):
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

    def try_some_code(self, code, args):
        """Run some coroutine testing code and see that it was all covered."""

        self.make_file("try_it.py", code)

        out = self.run_command("coverage run --timid %s try_it.py" % args)
        expected_out = "%d\n" % (sum(range(self.LIMIT)))
        self.assertEqual(out, expected_out)

        # Read the coverage file and see that try_it.py has all its lines
        # executed.
        data = coverage.CoverageData()
        data.read_file(".coverage")

        # If the test fails, it's helpful to see this info:
        fname = os.path.abspath("try_it.py")
        linenos = data.executed_lines(fname).keys()
        print("{0}: {1}".format(len(linenos), linenos))
        print_simple_annotation(code, linenos)

        lines = line_count(code)
        self.assertEqual(data.summary()['try_it.py'], lines)

    def test_threads(self):
        self.try_some_code(self.THREAD, "")

    def test_eventlet(self):
        if eventlet is None:
            raise SkipTest("No eventlet available")

        self.try_some_code(self.EVENTLET, "--coroutine=eventlet")

    def test_gevent(self):
        raise SkipTest("Still not sure why gevent isn't working...")

        if gevent is None:
            raise SkipTest("No gevent available")

        self.try_some_code(self.GEVENT, "--coroutine=gevent")


def print_simple_annotation(code, linenos):
    """Print the lines in `code` with X for each line number in `linenos`."""
    for lineno, line in enumerate(code.splitlines(), start=1):
        print(" {0:s} {1}".format("X" if lineno in linenos else " ", line))
