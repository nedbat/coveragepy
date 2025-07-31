# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Invasive patches for coverage.py"""

from __future__ import annotations

import atexit
import os

from typing import Any, Callable, NoReturn, TYPE_CHECKING

from coverage import env
from coverage.exceptions import ConfigError, CoverageException
from coverage.files import create_pth_file

if TYPE_CHECKING:
    from coverage import Coverage
    from coverage.config import CoverageConfig


def apply_patches(cov: Coverage, config: CoverageConfig, *, make_pth_file: bool=True) -> None:
    """Apply invasive patches requested by `[run] patch=`."""

    for patch in sorted(set(config.patch)):
        if patch == "_exit":

            def make_exit_patch(
                old_exit: Callable[[int], NoReturn],
            ) -> Callable[[int], NoReturn]:
                def coverage_os_exit_patch(status: int) -> NoReturn:
                    try:
                        cov.save()
                    except:  # pylint: disable=bare-except
                        pass
                    old_exit(status)

                return coverage_os_exit_patch

            os._exit = make_exit_patch(os._exit)  # type: ignore[assignment]

        elif patch == "execv":
            if env.WINDOWS:
                raise CoverageException("patch=execv isn't supported yet on Windows.")

            def make_execv_patch(fname: str, old_execv: Any) -> Any:
                def coverage_execv_patch(*args: Any, **kwargs: Any) -> Any:
                    try:
                        cov.save()
                    except:  # pylint: disable=bare-except
                        pass

                    if fname.endswith("e"):
                        # Assume the `env` argument is passed positionally.
                        new_env = args[-1]
                        # Pass our environment variable in the new environment.
                        new_env["COVERAGE_PROCESS_START"] = config.config_file
                        if env.TESTING:
                            # The subprocesses need to use the same core as the main process.
                            new_env["COVERAGE_CORE"] = os.getenv("COVERAGE_CORE")

                            # When testing locally, we need to honor the pyc file location
                            # or they get written to the .tox directories and pollute the
                            # next run with a different core.
                            if (
                                cache_prefix := os.getenv("PYTHONPYCACHEPREFIX")
                            ) is not None:
                                new_env["PYTHONPYCACHEPREFIX"] = cache_prefix

                            # Without this, it fails on PyPy and Ubuntu.
                            new_env["PATH"] = os.getenv("PATH")
                    old_execv(*args, **kwargs)

                return coverage_execv_patch

            # All the exec* and spawn* functions eventually call execv or execve.
            os.execv = make_execv_patch("execv", os.execv)
            os.execve = make_execv_patch("execve", os.execve)

        elif patch == "subprocess":
            if make_pth_file:
                pth_file = create_pth_file()
                assert pth_file is not None
                atexit.register(pth_file.unlink, missing_ok=True)
            assert config.config_file is not None
            os.environ["COVERAGE_PROCESS_START"] = config.config_file

        else:
            raise ConfigError(f"Unknown patch {patch!r}")
