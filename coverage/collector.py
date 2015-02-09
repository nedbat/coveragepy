"""Raw data collector for Coverage."""

import os, sys

from coverage import env
from coverage.misc import CoverageException
from coverage.pytracer import PyTracer

try:
    # Use the C extension code when we can, for speed.
    from coverage.tracer import CTracer         # pylint: disable=no-name-in-module
except ImportError:
    # Couldn't import the C extension, maybe it isn't built.
    if os.getenv('COVERAGE_TEST_TRACER') == 'c':
        # During testing, we use the COVERAGE_TEST_TRACER environment variable
        # to indicate that we've fiddled with the environment to test this
        # fallback code.  If we thought we had a C tracer, but couldn't import
        # it, then exit quickly and clearly instead of dribbling confusing
        # errors. I'm using sys.exit here instead of an exception because an
        # exception here causes all sorts of other noise in unittest.
        sys.stderr.write(
            "*** COVERAGE_TEST_TRACER is 'c' but can't import CTracer!\n"
            )
        sys.exit(1)
    CTracer = None


class Collector(object):
    """Collects trace data.

    Creates a Tracer object for each thread, since they track stack
    information.  Each Tracer points to the same shared data, contributing
    traced data points.

    When the Collector is started, it creates a Tracer for the current thread,
    and installs a function to create Tracers for each new thread started.
    When the Collector is stopped, all active Tracers are stopped.

    Threads started while the Collector is stopped will never have Tracers
    associated with them.

    """

    # The stack of active Collectors.  Collectors are added here when started,
    # and popped when stopped.  Collectors on the stack are paused when not
    # the top, and resumed when they become the top again.
    _collectors = []

    def __init__(self,
        should_trace, check_include, timid, branch, warn, concurrency,
    ):
        """Create a collector.

        `should_trace` is a function, taking a filename, and returning a
        canonicalized filename, or None depending on whether the file should
        be traced or not.

        TODO: `check_include`

        If `timid` is true, then a slower simpler trace function will be
        used.  This is important for some environments where manipulation of
        tracing functions make the faster more sophisticated trace function not
        operate properly.

        If `branch` is true, then branches will be measured.  This involves
        collecting data on which statements followed each other (arcs).  Use
        `get_arc_data` to get the arc data.

        `warn` is a warning function, taking a single string message argument,
        to be used if a warning needs to be issued.

        `concurrency` is a string indicating the concurrency library in use.
        Valid values are "greenlet", "eventlet", "gevent", or "thread" (the
        default).

        """
        self.should_trace = should_trace
        self.check_include = check_include
        self.warn = warn
        self.branch = branch
        self.threading = None
        self.concurrency = concurrency

        self.concur_id_func = None

        try:
            if concurrency == "greenlet":
                import greenlet                 # pylint: disable=import-error
                self.concur_id_func = greenlet.getcurrent
            elif concurrency == "eventlet":
                import eventlet.greenthread     # pylint: disable=import-error
                self.concur_id_func = eventlet.greenthread.getcurrent
            elif concurrency == "gevent":
                import gevent                   # pylint: disable=import-error
                self.concur_id_func = gevent.getcurrent
            elif concurrency == "thread" or not concurrency:
                # It's important to import threading only if we need it.  If
                # it's imported early, and the program being measured uses
                # gevent, then gevent's monkey-patching won't work properly.
                import threading
                self.threading = threading
            else:
                raise CoverageException(
                    "Don't understand concurrency=%s" % concurrency
                )
        except ImportError:
            raise CoverageException(
                "Couldn't trace with concurrency=%s, "
                "the module isn't installed." % concurrency
            )

        self.reset()

        if timid:
            # Being timid: use the simple Python trace function.
            self._trace_class = PyTracer
        else:
            # Being fast: use the C Tracer if it is available, else the Python
            # trace function.
            self._trace_class = CTracer or PyTracer

        self.supports_plugins = self._trace_class is CTracer

    def __repr__(self):
        return "<Collector at 0x%x>" % id(self)

    def tracer_name(self):
        """Return the class name of the tracer we're using."""
        return self._trace_class.__name__

    def reset(self):
        """Clear collected data, and prepare to collect more."""
        # A dictionary mapping filenames to dicts with line number keys,
        # or mapping filenames to dicts with line number pairs as keys.
        self.data = {}

        self.plugin_data = {}

        # A cache of the results from should_trace, the decision about whether
        # to trace execution in a file. A dict of filename to (filename or
        # None).
        if env.PYPY:
            import __pypy__                     # pylint: disable=import-error
            # Alex Gaynor said:
            # should_trace_cache is a strictly growing key: once a key is in
            # it, it never changes.  Further, the keys used to access it are
            # generally constant, given sufficient context. That is to say, at
            # any given point _trace() is called, pypy is able to know the key.
            # This is because the key is determined by the physical source code
            # line, and that's invariant with the call site.
            #
            # This property of a dict with immutable keys, combined with
            # call-site-constant keys is a match for PyPy's module dict,
            # which is optimized for such workloads.
            #
            # This gives a 20% benefit on the workload described at
            # https://bitbucket.org/pypy/pypy/issue/1871/10x-slower-than-cpython-under-coverage
            self.should_trace_cache = __pypy__.newdict("module")
        else:
            self.should_trace_cache = {}

        # Our active Tracers.
        self.tracers = []

    def _start_tracer(self):
        """Start a new Tracer object, and store it in self.tracers."""
        tracer = self._trace_class()
        tracer.data = self.data
        tracer.arcs = self.branch
        tracer.should_trace = self.should_trace
        tracer.should_trace_cache = self.should_trace_cache
        tracer.warn = self.warn

        if hasattr(tracer, 'concur_id_func'):
            tracer.concur_id_func = self.concur_id_func
        elif self.concur_id_func:
            raise CoverageException(
                "Can't support concurrency=%s with %s, "
                "only threads are supported" % (
                    self.concurrency, self.tracer_name(),
                )
            )

        if hasattr(tracer, 'plugin_data'):
            tracer.plugin_data = self.plugin_data
        if hasattr(tracer, 'threading'):
            tracer.threading = self.threading
        if hasattr(tracer, 'check_include'):
            tracer.check_include = self.check_include

        fn = tracer.start()
        self.tracers.append(tracer)

        return fn

    # The trace function has to be set individually on each thread before
    # execution begins.  Ironically, the only support the threading module has
    # for running code before the thread main is the tracing function.  So we
    # install this as a trace function, and the first time it's called, it does
    # the real trace installation.

    def _installation_trace(self, frame_unused, event_unused, arg_unused):
        """Called on new threads, installs the real tracer."""
        # Remove ourselves as the trace function
        sys.settrace(None)
        # Install the real tracer.
        fn = self._start_tracer()
        # Invoke the real trace function with the current event, to be sure
        # not to lose an event.
        if fn:
            fn = fn(frame_unused, event_unused, arg_unused)
        # Return the new trace function to continue tracing in this scope.
        return fn

    def start(self):
        """Start collecting trace information."""
        if self._collectors:
            self._collectors[-1].pause()
        self._collectors.append(self)

        # Check to see whether we had a fullcoverage tracer installed.
        traces0 = []
        fn0 = sys.gettrace()
        if fn0:
            tracer0 = getattr(fn0, '__self__', None)
            if tracer0:
                traces0 = getattr(tracer0, 'traces', [])

        # Install the tracer on this thread.
        fn = self._start_tracer()

        # Replay all the events from fullcoverage into the new trace function.
        for args in traces0:
            (frame, event, arg), lineno = args
            try:
                fn(frame, event, arg, lineno=lineno)
            except TypeError:
                raise Exception(
                    "fullcoverage must be run with the C trace function."
                )

        # Install our installation tracer in threading, to jump start other
        # threads.
        if self.threading:
            self.threading.settrace(self._installation_trace)

    def stop(self):
        """Stop collecting trace information."""
        assert self._collectors
        assert self._collectors[-1] is self

        self.pause()
        self.tracers = []

        # Remove this Collector from the stack, and resume the one underneath
        # (if any).
        self._collectors.pop()
        if self._collectors:
            self._collectors[-1].resume()

    def pause(self):
        """Pause tracing, but be prepared to `resume`."""
        for tracer in self.tracers:
            tracer.stop()
            stats = tracer.get_stats()
            if stats:
                print("\nCoverage.py tracer stats:")
                for k in sorted(stats.keys()):
                    print("%16s: %s" % (k, stats[k]))
        if self.threading:
            self.threading.settrace(None)

    def resume(self):
        """Resume tracing after a `pause`."""
        for tracer in self.tracers:
            tracer.start()
        if self.threading:
            self.threading.settrace(self._installation_trace)
        else:
            self._start_tracer()

    def get_line_data(self):
        """Return the line data collected.

        Data is { filename: { lineno: None, ...}, ...}

        """
        if self.branch:
            # If we were measuring branches, then we have to re-build the dict
            # to show line data.
            line_data = {}
            for f, arcs in self.data.items():
                line_data[f] = dict((l1, None) for l1, _ in arcs.keys() if l1)
            return line_data
        else:
            return self.data

    def get_arc_data(self):
        """Return the arc data collected.

        Data is { filename: { (l1, l2): None, ...}, ...}

        Note that no data is collected or returned if the Collector wasn't
        created with `branch` true.

        """
        if self.branch:
            return self.data
        else:
            return {}

    def get_plugin_data(self):
        return self.plugin_data
