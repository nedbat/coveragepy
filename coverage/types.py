# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""
Types for use throughout coverage.py.
"""

from types import ModuleType
from typing import (
    Any, Dict, Iterable, List, Optional, Tuple, Union,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    # Protocol is new in 3.8.  PYVERSIONS
    from typing import Protocol
else:
    class Protocol:             # pylint: disable=missing-class-docstring
        pass

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

# Line numbers are pervasive enough that they deserve their own type.
TLineNo = int

TArc = Tuple[TLineNo, TLineNo]

TMorf = Union[ModuleType, str]

TSourceTokenLines = Iterable[List[Tuple[str, str]]]

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
