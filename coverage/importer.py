# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""
Import system hooks for instrumenting source code for sys.monitoring.

Based on Slipcover's importer.py under the Apache license:
https://github.com/plasma-umass/slipcover/blob/28c637a786f938135ee8ffe7c4a1c788e13d92fa/src/slipcover/importer.py

Many thanks to Juan Altmayer Pizzorno and Emery Berger.

"""

from __future__ import annotations

import ast
import sys

from importlib.abc import MetaPathFinder, Loader
from importlib import machinery
from pathlib import Path
from typing import Any

from coverage.instrument import compile_instrumented


class InstrumentingLoader(Loader):
    def __init__(self, orig_loader: Loader, origin: str) -> None:
        self.orig_loader = orig_loader
        self.origin = Path(origin)

        # loadlib checks for this attribute to see if we support it... keep in sync with orig_loader
        if not getattr(self.orig_loader, "get_resource_reader", None):
            delattr(self, "get_resource_reader")

    # for compability with loaders supporting resources, used e.g. by sklearn
    def get_resource_reader(self, fullname: str):
        return self.orig_loader.get_resource_reader(fullname)

    def create_module(self, spec):
        return self.orig_loader.create_module(spec)

    def get_code(self, name):   # expected by pyrun
        return self.orig_loader.get_code(name)

    def exec_module(self, module):
        if isinstance(self.orig_loader, machinery.SourceFileLoader) and self.origin.exists():
            code = compile_instrumented(self.origin.read_bytes(), str(self.origin))
        else:
            code = self.orig_loader.get_code(module.__name__)

        exec(code, module.__dict__)


class InstrumentingMetaPathFinder(MetaPathFinder):
    def __init__(self):
        # TODO: pass in should_trace function
        pass

    def find_spec(self, fullname, path, target=None):

        for f in sys.meta_path:
            # skip ourselves
            if isinstance(f, self.__class__):
                continue

            if not hasattr(f, "find_spec"):
                continue

            spec = f.find_spec(fullname, path, target)
            if spec is None or spec.loader is None:
                continue

            # can't instrument extension files
            if isinstance(spec.loader, machinery.ExtensionFileLoader):
                return None

            #if self.file_matcher.matches(spec.origin):
            spec.loader = InstrumentingLoader(spec.loader, spec.origin)

            return spec

        return None


class InstrumentingImportManager:
    """A context manager that enables instrumentation while active."""

    def __init__(self):
        self.mpf = InstrumentingMetaPathFinder()

    def __enter__(self) -> InstrumentingImportManager:
        sys.meta_path.insert(0, self.mpf)
        return self

    def __exit__(self, *args: Any) -> None:
        # TODO: better way to remove the one?
        i = 0
        while i < len(sys.meta_path):
            if sys.meta_path[i] is self.mpf:
                sys.meta_path.pop(i)
                break
            i += 1
