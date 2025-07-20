# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Invasive patches for coverage.py"""

from __future__ import annotations

import atexit
import os

from typing import Callable, NoReturn, TYPE_CHECKING

from coverage.exceptions import ConfigError
from coverage.files import create_pth_file

if TYPE_CHECKING:
    from coverage import Coverage
    from coverage.config import CoverageConfig


def apply_patches(cov: Coverage, config: CoverageConfig) -> None:
    """Apply invasive patches requested by `[run] patch=`."""

    for patch in set(config.patch):
        if patch == "_exit":
            def make_patch(old_os_exit: Callable[[int], NoReturn]) -> Callable[[int], NoReturn]:
                def _coverage_os_exit_patch(status: int) -> NoReturn:
                    try:
                        cov.save()
                    except: # pylint: disable=bare-except
                        pass
                    old_os_exit(status)
                return _coverage_os_exit_patch
            os._exit = make_patch(os._exit)  # type: ignore[assignment]

        elif patch == "subprocess":
            pth_file = create_pth_file()
            assert pth_file is not None
            atexit.register(pth_file.unlink, missing_ok=True)
            assert config.config_file is not None
            os.environ["COVERAGE_PROCESS_START"] = config.config_file

        else:
            raise ConfigError(f"Unknown patch {patch!r}")
