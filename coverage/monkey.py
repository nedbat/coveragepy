"""Monkey-patching to make coverage work right in some cases."""

import multiprocessing
import multiprocessing.process
import sys

# An attribute that will be set on modules to indicate that they have been
# monkey-patched.
MARKER = "_coverage$patched"


def patch_multiprocessing():
    """Monkey-patch the multiprocessing module.

    This enables coverage measurement of processes started by multiprocessing.
    This is wildly experimental!

    """
    if hasattr(multiprocessing, MARKER):
        return

    if sys.version_info >= (3, 4):
        klass = multiprocessing.process.BaseProcess
    else:
        klass = multiprocessing.Process

    original_bootstrap = klass._bootstrap

    class ProcessWithCoverage(klass):
        """A replacement for multiprocess.Process that starts coverage."""
        def _bootstrap(self):
            from coverage import Coverage
            cov = Coverage(data_suffix=True)
            cov.start()
            try:
                return original_bootstrap(self)
            finally:
                cov.stop()
                cov.save()

    if sys.version_info >= (3, 4):
        klass._bootstrap = ProcessWithCoverage._bootstrap
    else:
        multiprocessing.Process = ProcessWithCoverage

    setattr(multiprocessing, MARKER, 1)
