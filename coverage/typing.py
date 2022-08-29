from __future__ import annotations

from typing import Protocol, Any, Callable, TypeVar
from typing_extensions import ParamSpec


class WarnCallable(Protocol):
    def __call__(self, msg: str, slug: str | None) -> None: ...


Fn = TypeVar("Fn", bound=Callable[..., Any])

P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")
