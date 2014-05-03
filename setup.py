# setup.py for coverage.py

"""Code coverage measurement for Python

Coverage.py measures code coverage, typically during test execution. It uses
the code analysis tools and tracing hooks provided in the Python standard
library to determine which lines are executable, and which have been executed.

Coverage.py runs on CPython 2.6, 2.7, 3.2, 3.3, or 3.4, and PyPy 2.2.

Documentation is at `nedbatchelder.com <%s>`_.  Code repository and issue
tracker are on `Bitbucket <http://bitbucket.org/ned/coveragepy>`_, with a
mirrored repo on `Github <https://github.com/nedbat/coveragepy>`_.

New in 3.7: ``--debug``, and 12 bugs closed.

New in 3.6: ``--fail-under``, and >20 bugs closed.

New in 3.5: Branch coverage exclusions, keyboard shortcuts in HTML report.

New in 3.4: Better control over source to measure, and unexecuted files
can be reported.

New in 3.3: .coveragerc files.

New in 3.2: Branch coverage!
"""

# This file is used unchanged under all versions of Python, 2.x and 3.x.

classifiers = """\
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
import os, sys

from setuptools import setup
from distutils.core import Extension        # pylint: disable=E0611,F0401
from distutils.command.build_ext import build_ext   # pylint: disable=E0611,F0401,C0301
from distutils import errors                # pylint: disable=E0611,F0401

# Get or massage our metadata.  We exec coverage/version.py so we can avoid
# importing the product code into setup.py.

doc = __doc__                   # __doc__ will be overwritten by version.py.
__version__ = __url__ = ""      # Keep pylint happy.

cov_ver_py = os.path.join(os.path.split(__file__)[0], "coverage/version.py")
with open(cov_ver_py) as version_file:
    exec(compile(version_file.read(), cov_ver_py, 'exec'))

doclines = (doc % __url__).splitlines()
classifier_list = classifiers.splitlines()

if 'a' in __version__:
    devstat = "3 - Alpha"
elif 'b' in __version__:
    devstat = "4 - Beta"
else:
    devstat = "5 - Production/Stable"
classifier_list.append("Development Status :: " + devstat)

# Install a script as "coverage", and as "coverage[23]", and as
# "coverage-2.7" (or whatever).
scripts = [
    'coverage = coverage:main',
    'coverage%d = coverage:main' % sys.version_info[:1],
    'coverage-%d.%d = coverage:main' % sys.version_info[:2],
    ]

# Create the keyword arguments for setup()

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

# A replacement for the build_ext command which raises a single exception
# if the build fails, so we can fallback nicely.

ext_errors = (
    errors.CCompilerError,
    errors.DistutilsExecError,
    errors.DistutilsPlatformError,
)
if sys.platform == 'win32':
    # distutils.msvc9compiler can raise an IOError when failing to
    # find the compiler
    ext_errors += (IOError,)

class BuildFailed(Exception):
    """Raise this to indicate the C extension wouldn't build."""
    def __init__(self):
        Exception.__init__(self)
        self.cause = sys.exc_info()[1] # work around py 2/3 different syntax

class ve_build_ext(build_ext):
    """Build C extensions, but fail with a straightforward exception."""

    def run(self):
        """Wrap `run` with `BuildFailed`."""
        try:
            build_ext.run(self)
        except errors.DistutilsPlatformError:
            raise BuildFailed()

    def build_extension(self, ext):
        """Wrap `build_extension` with `BuildFailed`."""
        try:
            # Uncomment to test compile failures:
            #   raise errors.CCompilerError("OOPS")
            build_ext.build_extension(self, ext)
        except ext_errors:
            raise BuildFailed()
        except ValueError as err:
            # this can happen on Windows 64 bit, see Python issue 7511
            if "'path'" in str(err): # works with both py 2/3
                raise BuildFailed()
            raise

# There are a few reasons we might not be able to compile the C extension.
# Figure out if we should attempt the C extension or not.

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
        cmdclass = {
            'build_ext': ve_build_ext,
            },
        ))

# Py3.x-specific details.

if sys.version_info >= (3, 0):
    setup_args.update(dict(
        use_2to3 = False,
        ))

def main():
    """Actually invoke setup() with the arguments we built above."""
    # For a variety of reasons, it might not be possible to install the C
    # extension.  Try it with, and if it fails, try it without.
    try:
        setup(**setup_args)
    except BuildFailed as exc:
        msg = "Couldn't install with extension module, trying without it..."
        exc_msg = "%s: %s" % (exc.__class__.__name__, exc.cause)
        print("**\n** %s\n** %s\n**" % (msg, exc_msg))

        del setup_args['ext_modules']
        setup(**setup_args)

if __name__ == '__main__':
    main()
