"""Raw data collector for Coverage."""

import sys, threading

try:
    # Use the C extension code when we can, for speed.
    from coverage.tracer import Tracer
except ImportError:
    # If we don't have the C tracer, use this Python one.
    class Tracer:
        """Python implementation of the raw data tracer."""
        def __init__(self):
            self.data = None
            self.should_trace = None
            self.should_trace_cache = None
            self.cur_filename = None
            self.filename_stack = []
            
        def _global_trace(self, frame, event, arg_unused):
            """The trace function passed to sys.settrace."""
            if event == 'call':
                # Entering a new function context.  Decide if we should trace
                # in this file.
                filename = frame.f_code.co_filename
                tracename = self.should_trace_cache.get(filename)
                if tracename is None:
                    tracename = self.should_trace(filename)
                    self.should_trace_cache[filename] = tracename
                if tracename:
                    # We need to trace.  Push the current filename on the stack
                    # and record the new current filename.
                    self.filename_stack.append(self.cur_filename)
                    self.cur_filename = tracename
                    # Use _local_trace for tracing within this function.
                    return self._local_trace
                else:
                    # No tracing in this function.
                    return None
            return self._global_trace

        def _local_trace(self, frame, event, arg_unused):
            """The trace function used within a function."""
            if event == 'line':
                # Record an executed line.
                self.data[(self.cur_filename, frame.f_lineno)] = True
            elif event == 'return':
                # Leaving this function, pop the filename stack.
                self.cur_filename = self.filename_stack.pop()
            return self._local_trace

        def start(self):
            """Start this Tracer."""
            sys.settrace(self._global_trace)

        def stop(self):
            """Stop this Tracer."""
            sys.settrace(None)

class Collector:
    """Collects trace data.

    Creates a Tracer object for each thread, since they track stack information.
    Each Tracer points to the same shared data, contributing traced data points.
    
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

    def __init__(self, should_trace):
        """Create a collector.
        
        `should_trace` is a function, taking a filename, and returning a
        canonicalized filename, or False depending on whether the file should
        be traced or not.
        
        """
        self.should_trace = should_trace
        self.reset()

    def reset(self):
        """Clear collected data, and prepare to collect more."""
        # A dictionary with an entry for (Python source file name, line number
        # in that file) if that line has been executed.
        self.data = {}
        
        # A cache of the results from should_trace, the decision about whether
        # to trace execution in a file. A dict of filename to (filename or
        # False).
        self.should_trace_cache = {}

        # Our active Tracers.
        self.tracers = []

    def _start_tracer(self):
        """Start a new Tracer object, and store it in self.tracers."""
        tracer = Tracer()
        tracer.data = self.data
        tracer.should_trace = self.should_trace
        tracer.should_trace_cache = self.should_trace_cache
        tracer.start()
        self.tracers.append(tracer)

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
        self._start_tracer()
        # Return None to reiterate that we shouldn't be used for tracing.
        return None

    def start(self):
        """Start collecting trace information."""
        if self._collectors:
            self._collectors[-1]._pause()
        self._collectors.append(self)
        # Install the tracer on this thread.
        self._start_tracer()
        # Install our installation tracer in threading, to jump start other
        # threads.
        threading.settrace(self._installation_trace)

    def stop(self):
        """Stop collecting trace information."""
        assert self._collectors
        assert self._collectors[-1] is self
        
        for tracer in self.tracers:
            tracer.stop()
        self.tracers = []
        threading.settrace(None)
        
        # Remove this Collector from the stack, and resume the one underneath
        # (if any).
        self._collectors.pop()
        if self._collectors:
            self._collectors[-1]._resume()

    def _pause(self):
        """Stop tracing, but be prepared to _resume."""
        for tracer in self.tracers:
            tracer.stop()
        threading.settrace(None)
        
    def _resume(self):
        """Resume tracing after a _pause."""
        for tracer in self.tracers:
            tracer.start()
        threading.settrace(self._installation_trace)

    def data_points(self):
        """Return the (filename, lineno) pairs collected."""
        return self.data.keys()
