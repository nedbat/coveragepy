# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Invasive patches for coverage.py"""

from __future__ import annotations

import atexit
import os

from typing import NoReturn, TYPE_CHECKING

from coverage.exceptions import ConfigError
from coverage.files import create_pth_file

if TYPE_CHECKING:
    from coverage import Coverage
    from coverage.config import CoverageConfig

_old_os_exit = os._exit

def apply_patches(cov: Coverage, config: CoverageConfig) -> None:
    """Apply invasive patches requested by `[run] patch=`."""

    for patch in set(config.patch):
        if patch == "_exit":
            def _coverage_os_exit_patch(status: int) -> NoReturn:
                try:
                    cov.save()
                except: # pylint: disable=bare-except
                    pass
                _old_os_exit(status)
            os._exit = _coverage_os_exit_patch
        elif patch == "subprocess":
            pth_file = create_pth_file()
            assert pth_file is not None
            atexit.register(pth_file.unlink, missing_ok=True)
            assert config.config_file is not None
            os.environ["COVERAGE_PROCESS_START"] = config.config_file
        else:
            raise ConfigError(f"Unknown patch {patch!r}")
