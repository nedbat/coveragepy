# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Monkey-patching to add Twisted support for coverage.py
"""

from functools import partial
from tempfile import mkdtemp
from os.path import join

# XXX do it without installing the default reactor
import twisted.internet.reactor

from coverage.misc import contract

# An attribute that will be set on the module to indicate that it has been
# monkey-patched.  Value copied from multiproc.py.
PATCHED_MARKER = "_coverage$patched"

@contract(rcfile=str)
def patch_twisted(rcfile):
    """
    The twisted.internet.interfaces.IReactorProcess.spawnProcess
    implementation of the Twisted reactor is patched to enable coverage
    collection in spawned processes.

    This works by clobbering sitecustomize.
    """
    if getattr(twisted.internet, PATCHED_MARKER, False):
        return

    origSpawnProcess = twisted.internet.reactor.spawnProcess
    twisted.internet.reactor.spawnProcess = partial(
        _coverageSpawnProcess,
        origSpawnProcess,
        rcfile,
    )
    setattr(twisted.internet, PATCHED_MARKER, True)


def _coverageSpawnProcess(
    origSpawnProcess,
    rcfile,
    processProtocol,
    executable,
    args=(),
    env=None,
    *a,
    **kw
):
    """
    Spawn a process using ``origSpawnProcess``.  Set up its environment so
    that coverage its collected, if it is a Python process.
    """
    if env is None:
        env = os.environ.copy()
    pythonpath = env.get(u"PYTHONPATH", u"").split(u":")
    dtemp = mkdtemp()
    pythonpath.insert(0, dtemp)
    sitecustomize = join(dtemp, u"sitecustomize.py")
    with open(sitecustomize, "wt") as f:
        f.write("""\
import sys, os.path
sys.path.remove({dtemp!r})
os.remove({sitecustomize!r})
if os.path.exists({sitecustomizec!r}):
    os.remove({sitecustomizec!r})
os.rmdir({dtemp!r})
import coverage
coverage.process_startup()
""".format(
    sitecustomize=sitecustomize,
    sitecustomizec=sitecustomize + u"c",
    dtemp=dtemp,
))
        env[u"PYTHONPATH"] = u":".join(pythonpath)
        env[u"COVERAGE_PROCESS_START"] = rcfile
    return origSpawnProcess(
        processProtocol,
        executable,
        args,
        env,
        *a,
        **kw
    )
