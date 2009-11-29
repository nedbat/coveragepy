"""Coverage-test Coverage itself."""

import coverage
import os, shutil, sys

HTML_DIR = "htmlcov"

if os.path.exists(HTML_DIR):
    shutil.rmtree(HTML_DIR)

cov = coverage.coverage(branch=True)
# Cheap trick: the coverage code itself is excluded from measurement, but if
# we clobber the cover_prefix in the coverage object, we can defeat the
# self-detection.
cov.cover_prefix = "Please measure coverage.py!"
cov.erase()
cov.start()

# Re-import coverage to get it coverage tested!  I don't understand all the
# mechanics here, but if I don't carry over the imported modules (in covmods),
# then things go haywire (os == None eventually).
covmods = {}
covdir = os.path.split(coverage.__file__)
for name, mod in sys.modules.items():
    if name.startswith('coverage'):
        if hasattr(mod, '__file__') and mod.__file__.startswith(covdir):
            covmods[name] = mod
            del sys.modules[name]
import coverage     # don't warn about re-import: pylint: disable-msg=W0404
sys.modules.update(covmods)

# Run nosetests, with the arguments from our command line.
nose_args = sys.argv[1:]
print(":: Running nosetests %s" % " ".join(nose_args))
import nose
nose.run(nose_args)

cov.stop()
print(":: Saving .coverage")
cov.save()

print(":: Writing HTML report to %s/index.html" % HTML_DIR)
cov.clear_exclude()
cov.exclude("#pragma: no cover")
cov.exclude("def __repr__")
cov.exclude("if __name__ == .__main__.:")
cov.exclude("raise AssertionError")

cov.html_report(directory=HTML_DIR, ignore_errors=True, omit_prefixes=["mock"])
