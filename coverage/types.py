# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""
Types for use throughout coverage.py.
"""

from __future__ import annotations

from types import FrameType, ModuleType
from typing import (
    Any, Callable, Dict, Iterable, List, Mapping, Optional, Set, Tuple, Union,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    # Protocol is new in 3.8.  PYVERSIONS
    from typing import Protocol

    from coverage.plugin import FileTracer

else:
    class Protocol:             # pylint: disable=missing-class-docstring
        pass

## Python tracing

class TTraceFn(Protocol):
    """A Python trace function."""
    def __call__(
        self,
        frame: FrameType,
        event: str,
        arg: Any,
        lineno: Optional[int]=None  # Our own twist, see collector.py
    ) -> TTraceFn:
        ...

## Coverage.py tracing

# Line numbers are pervasive enough that they deserve their own type.
TLineNo = int

TArc = Tuple[TLineNo, TLineNo]

class TFileDisposition(Protocol):
    """A simple value type for recording what to do with a file."""

    original_filename: str
    canonical_filename: str
    source_filename: Optional[str]
    trace: bool
    reason: str
    file_tracer: Optional[FileTracer]
    has_dynamic_filename: bool


# When collecting data, we use a dictionary with a few possible shapes. The
# keys are always file names.
# - If measuring line coverage, the values are sets of line numbers.
# - If measuring arcs in the Python tracer, the values are sets of arcs (pairs
#   of line numbers).
# - If measuring arcs in the C tracer, the values are sets of packed arcs (two
#   line numbers combined into one integer).

TTraceData = Union[
    Dict[str, Set[TLineNo]],
    Dict[str, Set[TArc]],
    Dict[str, Set[int]],
]

class TTracer(Protocol):
    """Either CTracer or PyTracer."""

    data: TTraceData
    trace_arcs: bool
    should_trace: Callable[[str, FrameType], TFileDisposition]
    should_trace_cache: Mapping[str, Optional[TFileDisposition]]
    should_start_context: Optional[Callable[[FrameType], Optional[str]]]
    switch_context: Optional[Callable[[Optional[str]], None]]
    warn: TWarnFn

    def __init__(self) -> None:
        ...

    def start(self) -> TTraceFn:
        """Start this tracer, returning a trace function."""

    def stop(self) -> None:
        """Stop this tracer."""

    def activity(self) -> bool:
        """Has there been any activity?"""

    def reset_activity(self) -> None:
        """Reset the activity() flag."""

    def get_stats(self) -> Optional[Dict[str, int]]:
        """Return a dictionary of statistics, or None."""

## Coverage

# Many places use kwargs as Coverage kwargs.
TCovKwargs = Any


## Configuration

# One value read from a config file.
TConfigValue = Optional[Union[bool, int, float, str, List[str]]]
# An entire config section, mapping option names to values.
TConfigSection = Dict[str, TConfigValue]

class TConfigurable(Protocol):
    """Something that can proxy to the coverage configuration settings."""

    def get_option(self, option_name: str) -> Optional[TConfigValue]:
        """Get an option from the configuration.

        `option_name` is a colon-separated string indicating the section and
        option name.  For example, the ``branch`` option in the ``[run]``
        section of the config file would be indicated with `"run:branch"`.

        Returns the value of the option.

        """

    def set_option(self, option_name: str, value: Union[TConfigValue, TConfigSection]) -> None:
        """Set an option in the configuration.

        `option_name` is a colon-separated string indicating the section and
        option name.  For example, the ``branch`` option in the ``[run]``
        section of the config file would be indicated with `"run:branch"`.

        `value` is the new value for the option.

        """

## Parsing

TMorf = Union[ModuleType, str]

TSourceTokenLines = Iterable[List[Tuple[str, str]]]

## Plugins

class TPlugin(Protocol):
    """What all plugins have in common."""
    _coverage_plugin_name: str
    _coverage_enabled: bool


## Debugging

class TWarnFn(Protocol):
    """A callable warn() function."""
    def __call__(self, msg: str, slug: Optional[str]=None, once: bool=False,) -> None:
        ...


class TDebugCtl(Protocol):
    """A DebugControl object, or something like it."""

    def should(self, option: str) -> bool:
        """Decide whether to output debug information in category `option`."""

    def write(self, msg: str) -> None:
        """Write a line of debug output."""
