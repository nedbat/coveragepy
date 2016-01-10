# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

"""Monkey-patching to make coverage.py work right in some cases."""

import multiprocessing
import multiprocessing.process
import sys

# An attribute that will be set on modules to indicate that they have been
# monkey-patched.
PATCHED_MARKER = "_coverage$patched"

if sys.version_info >= (3, 4):
    klass = multiprocessing.process.BaseProcess
else:
    klass = multiprocessing.Process

original_bootstrap = klass._bootstrap


class ProcessWithCoverage(klass):
    """A replacement for multiprocess.Process that starts coverage."""
    def _bootstrap(self):
        """Wrapper around _bootstrap to start coverage."""
        from coverage import Coverage
        cov = Coverage(data_suffix=True)
        cov.start()
        try:
            return original_bootstrap(self)
        finally:
            cov.stop()
            cov.save()


class Stowaway(object):
    """An object to pickle, so when it is unpickled, it can apply the monkey-patch."""
    def __getstate__(self):
        return {}

    def __setstate__(self, state_unused):
        patch_multiprocessing()


def patch_multiprocessing():
    """Monkey-patch the multiprocessing module.

    This enables coverage measurement of processes started by multiprocessing.
    This is wildly experimental!

    """
    if hasattr(multiprocessing, PATCHED_MARKER):
        return

    if sys.version_info >= (3, 4):
        klass._bootstrap = ProcessWithCoverage._bootstrap
    else:
        multiprocessing.Process = ProcessWithCoverage

    # When spawning processes rather than forking them, we have no state in the
    # new process.  We sneak in there with a Stowaway: we stuff one of our own
    # objects into the data that gets pickled and sent to the sub-process. When
    # the Stowaway is unpickled, it's __setstate__ method is called, which
    # re-applies the monkey-patch.
    # Windows only spawns, so this is needed to keep Windows working.
    try:
        from multiprocessing import spawn           # pylint: disable=no-name-in-module
        original_get_preparation_data = spawn.get_preparation_data
    except (ImportError, AttributeError):
        pass
    else:
        def get_preparation_data_with_stowaway(name):
            """Get the original preparation data, and also insert our stowaway."""
            d = original_get_preparation_data(name)
            d['stowaway'] = Stowaway()
            return d

        spawn.get_preparation_data = get_preparation_data_with_stowaway

    setattr(multiprocessing, PATCHED_MARKER, True)
