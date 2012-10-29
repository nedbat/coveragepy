# setup.py for coverage.

"""Code coverage measurement for Python

Coverage.py measures code coverage, typically during test execution. It uses
the code analysis tools and tracing hooks provided in the Python standard
library to determine which lines are executable, and which have been executed.

Coverage.py runs on Pythons 2.3 through 3.3, and PyPy 1.8.

Documentation is at `nedbatchelder.com <%s>`_.  Code repository and issue
tracker are at `bitbucket.org <http://bitbucket.org/ned/coveragepy>`_.

New in 3.5: Branch coverage exclusions, keyboard shortcuts in HTML report.

New in 3.4: Better control over source to measure, and unexecuted files
can be reported.

New in 3.3: .coveragerc files.

New in 3.2: Branch coverage!

"""

# This file is used unchanged under all versions of Python, 2.x and 3.x.

classifiers = """
Environment :: Console
Intended Audience :: Developers
License :: OSI Approved :: BSD License
Operating System :: OS Independent
Programming Language :: Python :: 2
Programming Language :: Python :: 3
Topic :: Software Development :: Quality Assurance
Topic :: Software Development :: Testing
"""

# Pull in the tools we need.
import sys

# Distribute is a new fork of setuptools.  It's supported on Py3.x, so we use
# it there, but stick with classic setuptools on Py2.x until Distribute becomes
# more accepted.
if sys.version_info >= (3, 0):
    from distribute_setup import use_setuptools
else:
    from ez_setup import use_setuptools

use_setuptools()

from setuptools import setup
from distutils.core import Extension    # pylint: disable=E0611,F0401

# Get or massage our metadata.

from coverage import __url__, __version__

scripts = ['coverage = coverage:main']
if sys.version_info >= (3, 0):
    scripts.append('coverage3 = coverage:main')

doclines = (__doc__ % __url__).split('\n')

classifier_list = [c for c in classifiers.split("\n") if c]

if 'a' in __version__:
    devstat = "3 - Alpha"
elif 'b' in __version__:
    devstat = "4 - Beta"
else:
    devstat = "5 - Production/Stable"
classifier_list.append("Development Status :: " + devstat)

# Set it up!

setup_args = dict(
    name = 'coverage',
    version = __version__,

    packages = [
        'coverage',
        ],

    package_data = {
        'coverage': [
            'htmlfiles/*.*',
            ]
        },

    entry_points = {'console_scripts': scripts},

    # We need to get HTML assets from our htmlfiles dir.
    zip_safe = False,

    author = 'Ned Batchelder and others',
    author_email = 'ned@nedbatchelder.com',
    description = doclines[0],
    long_description = '\n'.join(doclines[2:]),
    keywords = 'code coverage testing',
    license = 'BSD',
    classifiers = classifier_list,
    url = __url__,
    )

# There are a few reasons we might not be able to compile the C extension.

compile_extension = True

if sys.platform.startswith('java'):
    # Jython can't compile C extensions
    compile_extension = False

if '__pypy__' in sys.builtin_module_names:
    # Pypy can't compile C extensions
    compile_extension = False

if compile_extension:
    setup_args.update(dict(
        ext_modules = [
            Extension("coverage.tracer", sources=["coverage/tracer.c"])
            ],
        ))

if sys.version_info >= (3, 0):
    setup_args.update(dict(
        use_2to3=False,
        ))

# For a variety of reasons, it might not be possible to install the C
# extension.  Try it with, and if it fails, try it without.
try:
    setup(**setup_args)
except:     # pylint: disable=W0702
    # When setup() can't compile, it tries to exit.  We'll catch SystemExit
    # here :-(, and try again.
    if 'install' not in sys.argv or 'ext_modules' not in setup_args:
        # We weren't trying to install an extension, so forget it.
        raise
    msg = "Couldn't install with extension module, trying without it..."
    exc = sys.exc_info()[1]
    exc_msg = "%s: %s" % (exc.__class__.__name__, exc)
    print("**\n** %s\n** %s\n**" % (msg, exc_msg))

    del setup_args['ext_modules']
    setup(**setup_args)
