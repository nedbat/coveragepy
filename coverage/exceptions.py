# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Exceptions coverage.py can raise."""


class BaseCoverageException(Exception):
    """The base of all Coverage exceptions."""
    pass


class CoverageException(BaseCoverageException):
    """An exception raised by a coverage.py function."""
    pass


class NoSource(CoverageException):
    """We couldn't find the source for a module."""
    pass


class NoCode(NoSource):
    """We couldn't find any code at all."""
    pass


class NotPython(CoverageException):
    """A source file turned out not to be parsable Python."""
    pass


class ExceptionDuringRun(CoverageException):
    """An exception happened while running customer code.

    Construct it with three arguments, the values from `sys.exc_info`.

    """
    pass


class StopEverything(BaseCoverageException):
    """An exception that means everything should stop.

    The CoverageTest class converts these to SkipTest, so that when running
    tests, raising this exception will automatically skip the test.

    """
    pass


class CoverageWarning(Warning):
    """A warning from Coverage.py."""
    pass
