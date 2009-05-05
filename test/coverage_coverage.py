# Coverage-test Coverage itself.

import coverage
import os, shutil, sys

HTML_DIR = "htmlcov"

if os.path.exists(HTML_DIR):
    shutil.rmtree(HTML_DIR)

cov = coverage.coverage()
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
import coverage
sys.modules.update(covmods)

# Run nosetests, with the arguments from our command line.
import nose
nose.run(sys.argv[1:])

cov.stop()
cov.save()  # TODO: This is needed to get group_collected_data called.

cov.clear_exclude()
cov.exclude("#pragma: no cover")
cov.exclude("def __repr__")
cov.exclude("if __name__ == .__main__.:")

cov.html_report(directory=HTML_DIR, ignore_errors=True)
