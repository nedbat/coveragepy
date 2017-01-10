# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

"""Control of and utilities for debugging."""

import contextlib
import inspect
import os
import re
import sys
try:
    import _thread
except ImportError:
    import thread as _thread

from coverage.misc import isolate_module

os = isolate_module(os)


# When debugging, it can be helpful to force some options, especially when
# debugging the configuration mechanisms you usually use to control debugging!
# This is a list of forced debugging options.
FORCED_DEBUG = []

# A hack for debugging testing in sub-processes.
_TEST_NAME_FILE = ""    # "/tmp/covtest.txt"


class DebugControl(object):
    """Control and output for debugging."""

    def __init__(self, options, output):
        """Configure the options and output file for debugging."""
        self.options = options
        self.output = output
        self.suppress_callers = False

    def __repr__(self):
        return "<DebugControl options=%r output=%r>" % (self.options, self.output)

    def should(self, option):
        """Decide whether to output debug information in category `option`."""
        if option == "callers" and self.suppress_callers:
            return False
        return (option in self.options or option in FORCED_DEBUG)

    @contextlib.contextmanager
    def without_callers(self):
        """A context manager to prevent call stacks from being logged."""
        old = self.suppress_callers
        self.suppress_callers = True
        try:
            yield
        finally:
            self.suppress_callers = old

    def write(self, msg):
        """Write a line of debug output.

        `msg` is the line to write. A newline will be appended.

        """
        if self.should('pid'):
            msg = "pid %5d: %s" % (os.getpid(), msg)
        self.output.write(msg+"\n")
        if self.should('callers'):
            dump_stack_frames(out=self.output, skip=1)
        self.output.flush()

    def write_formatted_info(self, header, info):
        """Write a sequence of (label,data) pairs nicely."""
        self.write(info_header(header))
        for line in info_formatter(info):
            self.write(" %s" % line)


def info_header(label):
    """Make a nice header string."""
    return "--{0:-<60s}".format(" "+label+" ")


def info_formatter(info):
    """Produce a sequence of formatted lines from info.

    `info` is a sequence of pairs (label, data).  The produced lines are
    nicely formatted, ready to print.

    """
    info = list(info)
    if not info:
        return
    label_len = max(len(l) for l, _d in info)
    for label, data in info:
        if data == []:
            data = "-none-"
        if isinstance(data, (list, set, tuple)):
            prefix = "%*s:" % (label_len, label)
            for e in data:
                yield "%*s %s" % (label_len+1, prefix, e)
                prefix = ""
        else:
            yield "%*s: %s" % (label_len, label, data)


def short_stack(limit=None, skip=0):
    """Return a string summarizing the call stack.

    The string is multi-line, with one line per stack frame. Each line shows
    the function name, the file name, and the line number:

        ...
        start_import_stop : /Users/ned/coverage/trunk/tests/coveragetest.py @95
        import_local_file : /Users/ned/coverage/trunk/tests/coveragetest.py @81
        import_local_file : /Users/ned/coverage/trunk/coverage/backward.py @159
        ...

    `limit` is the number of frames to include, defaulting to all of them.

    `skip` is the number of frames to skip, so that debugging functions can
    call this and not be included in the result.

    """
    stack = inspect.stack()[limit:skip:-1]
    return "\n".join("%30s : %s @%d" % (t[3], t[1], t[2]) for t in stack)


def dump_stack_frames(limit=None, out=None, skip=0):
    """Print a summary of the stack to stdout, or some place else."""
    out = out or sys.stdout
    out.write(short_stack(limit=limit, skip=skip+1))
    out.write("\n")


def short_id(id64):
    """Given a 64-bit id, make a shorter 16-bit one."""
    id16 = 0
    for offset in range(0, 64, 16):
        id16 ^= id64 >> offset
    return id16 & 0xFFFF


class DebugOutputFile(object):                              # pragma: debugging
    """A file-like object that includes pid and cwd information."""
    def __init__(self, outfile):
        self.outfile = outfile
        self.cwd = None

    SYS_MOD_NAME = '$coverage.debug.DebugOutputFile.the_one'

    @classmethod
    def the_one(cls):
        """Get the process-wide singleton DebugOutputFile."""
        # Because of the way igor.py deletes and re-imports modules,
        # this class can be defined more than once. But we really want
        # a process-wide singleton. So stash it in sys.modules instead of
        # on a class attribute. Yes, this is aggressively gross.
        the_one = sys.modules.get(cls.SYS_MOD_NAME)
        if the_one is None:
            filename = os.environ.get("COVERAGE_LOG", "/tmp/covlog.txt")
            sys.modules[cls.SYS_MOD_NAME] = the_one = cls(open(filename, "a"))

            cmd = " ".join(getattr(sys, 'argv', ['???']))
            the_one._write("New process: executable: %s\n" % (sys.executable,))
            the_one._write("New process: cmd: %s\n" % (cmd,))
            if hasattr(os, 'getppid'):
                the_one._write("New process: parent pid: %s\n" % (os.getppid(),))

        return the_one

    def write(self, text, stack=False):
        """Just like file.write"""
        cwd = os.getcwd()
        if cwd != self.cwd:
            self._write("cwd is now {0!r}\n".format(cwd))
            self.cwd = cwd
        self._write(text, stack=stack)

    def _write(self, text, stack=False):
        """The raw text-writer, so that we can use it ourselves."""
        # Thread ids are useful, but too long. Make a shorter one.
        tid = "{0:04x}".format(short_id(_thread.get_ident()))

        # Aspectlib prints stack traces, but includes its own frames.  Scrub those out:
        # <<< aspectlib/__init__.py:257:function_wrapper < igor.py:143:run_tests < ...
        text = re.sub(r"(?<= )aspectlib/[^.]+\.py:\d+:\w+ < ", "", text)

        self.outfile.write("{0:5d}.{1}: {2}".format(os.getpid(), tid, text))
        self.outfile.flush()
        if stack:
            dump_stack_frames(out=self.outfile, skip=1)


def log(msg, stack=False):                                  # pragma: debugging
    """Write a log message as forcefully as possible."""
    DebugOutputFile.the_one().write(msg+"\n", stack=stack)


def enable_aspectlib_maybe():                               # pragma: debugging
    """For debugging, we can use aspectlib to trace execution.

    Define COVERAGE_ASPECTLIB to enable and configure aspectlib to trace
    execution::

        $ export COVERAGE_LOG=covaspect.txt
        $ export COVERAGE_ASPECTLIB=coverage.Coverage:coverage.data.CoverageData
        $ coverage run blah.py ...

    This will trace all the public methods on Coverage and CoverageData,
    writing the information to covaspect.txt.

    """
    aspects = os.environ.get("COVERAGE_ASPECTLIB", "")
    if not aspects:
        return

    import aspectlib                            # pylint: disable=import-error
    import aspectlib.debug                      # pylint: disable=import-error

    aspects_file = DebugOutputFile.the_one()
    aspect_log = aspectlib.debug.log(
        print_to=aspects_file, attributes=['id'], stacktrace=30, use_logging=False
    )
    public_methods = re.compile(r'^(__init__|[a-zA-Z].*)$')
    for aspect in aspects.split(':'):
        aspectlib.weave(aspect, aspect_log, methods=public_methods)
