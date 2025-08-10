# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Invasive patches for coverage.py."""

from __future__ import annotations

import atexit
import contextlib
import os
import site
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, NoReturn

from coverage import env
from coverage.exceptions import ConfigError, CoverageException

if TYPE_CHECKING:
    from coverage import Coverage
    from coverage.config import CoverageConfig
    from coverage.types import TDebugCtl


def apply_patches(
    cov: Coverage,
    config: CoverageConfig,
    debug: TDebugCtl,
    *,
    make_pth_file: bool = True,
) -> None:
    """Apply invasive patches requested by `[run] patch=`."""

    for patch in sorted(set(config.patch)):
        if patch == "_exit":
            if debug.should("patch"):
                debug.write("Patching _exit")

            def make_exit_patch(
                old_exit: Callable[[int], NoReturn],
            ) -> Callable[[int], NoReturn]:
                def coverage_os_exit_patch(status: int) -> NoReturn:
                    with contextlib.suppress(Exception):
                        if debug.should("patch"):
                            debug.write("Using _exit patch")
                    with contextlib.suppress(Exception):
                        cov.save()
                    old_exit(status)

                return coverage_os_exit_patch

            os._exit = make_exit_patch(os._exit)  # type: ignore[assignment]

        elif patch == "execv":
            if env.WINDOWS:
                raise CoverageException("patch=execv isn't supported yet on Windows.")

            if debug.should("patch"):
                debug.write("Patching execv")

            def make_execv_patch(fname: str, old_execv: Any) -> Any:
                def coverage_execv_patch(*args: Any, **kwargs: Any) -> Any:
                    with contextlib.suppress(Exception):
                        if debug.should("patch"):
                            debug.write(f"Using execv patch for {fname}")
                    with contextlib.suppress(Exception):
                        cov.save()

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
                            if (cache_prefix := os.getenv("PYTHONPYCACHEPREFIX")) is not None:
                                new_env["PYTHONPYCACHEPREFIX"] = cache_prefix

                            # Without this, it fails on PyPy and Ubuntu.
                            new_env["PATH"] = os.getenv("PATH")
                    old_execv(*args, **kwargs)

                return coverage_execv_patch

            # All the exec* and spawn* functions eventually call execv or execve.
            os.execv = make_execv_patch("execv", os.execv)
            os.execve = make_execv_patch("execve", os.execve)

        elif patch == "subprocess":
            if debug.should("patch"):
                debug.write("Patching subprocess")

            if make_pth_file:
                pth_files = create_pth_files()
                def make_deleter(pth_files: list[Path]) -> Callable[[], None]:
                    def delete_pth_files() -> None:
                        for p in pth_files:
                            p.unlink(missing_ok=True)
                    return delete_pth_files
                atexit.register(make_deleter(pth_files))
            assert config.config_file is not None
            os.environ["COVERAGE_PROCESS_START"] = config.config_file
            os.environ["COVERAGE_PROCESS_DATAFILE"] = os.path.abspath(config.data_file)

        else:
            raise ConfigError(f"Unknown patch {patch!r}")


# Writing .pth files is not obvious. On Windows, getsitepackages() returns two
# directories.  A .pth file in the first will be run, but coverage isn't
# importable yet.  We write into all the places we can, but with defensive
# import code.

PTH_CODE = """\
try:
    import coverage
except:
    pass
else:
    coverage.process_startup()
"""

def create_pth_files() -> list[Path]:
    """Create .pth files for measuring subprocesses."""
    pth_text = rf"import sys; exec({PTH_CODE!r})"
    pth_files = []
    for pth_dir in site.getsitepackages():
        pth_file = Path(pth_dir) / f"subcover_{os.getpid()}.pth"
        try:
            pth_file.write_text(pth_text, encoding="utf-8")
        except OSError:  # pragma: cant happen
            continue
        else:
            pth_files.append(pth_file)
    return pth_files
