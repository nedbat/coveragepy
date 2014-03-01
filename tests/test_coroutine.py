"""Tests for coroutining."""

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
    """How many non-blank lines are in `s`?"""
    return sum(1 for l in s.splitlines() if l.strip())


class CoroutineTest(CoverageTest):
    """Tests of the coroutine support in coverage.py."""

    # The code common to all the concurrency models. Don't use any comments,
    # we're counting non-blank lines to see they are all covered.
    COMMON = """
        class Producer(threading.Thread):
            def __init__(self, q):
                threading.Thread.__init__(self)
                self.q = q

            def run(self):
                for i in range(1000):
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

        q = Queue.Queue()
        c = Consumer(q)
        c.start()
        p = Producer(q)
        p.start()
        p.join()
        c.join()
        """

    # Import the things to use threads.
    THREAD = """\
        import threading
        try:
            import Queue
        except ImportError:
            # Python 3 :)
            import queue as Queue
        """ + COMMON

    # Import the things to use eventlet.
    EVENTLET = """\
        import eventlet.green.threading as threading
        import eventlet.queue as Queue
        """ + COMMON

    # Import the things to use gevent.
    GEVENT = """\
        from gevent import monkey
        monkey.patch_thread()
        import threading
        import gevent.queue as Queue
        """ + COMMON

    def try_some_code(self, code, args):
        """Run some coroutine testing code and see that it was all covered."""
        raise SkipTest("Need to put this on a back burner for a while...")
        self.make_file("try_it.py", code)

        out = self.run_command("coverage run %s try_it.py" % args)
        expected_out = "%d\n" % (sum(range(1000)))
        self.assertEqual(out, expected_out)

        # Read the coverage file and see that try_it.py has all its lines
        # executed.
        data = coverage.CoverageData()
        data.read_file(".coverage")
        lines = line_count(code)
        self.assertEqual(data.summary()['try_it.py'], lines)

    def test_threads(self):
        self.try_some_code(self.THREAD, "")

    def test_eventlet(self):
        if eventlet is None:
            raise SkipTest("No eventlet available")

        self.try_some_code(self.EVENTLET, "--coroutine=eventlet")

    def test_gevent(self):
        if gevent is None:
            raise SkipTest("No gevent available")

        self.try_some_code(self.GEVENT, "--coroutine=gevent")
