# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Code coverage measurement for Python"""

# Distutils setup for coverage.py
# This file is used unchanged under all versions of Python.

import os
import sys

# Setuptools has to be imported before distutils, or things break.
from setuptools import setup
from distutils.core import Extension                # pylint: disable=wrong-import-order
from setuptools.command.build_ext import build_ext  # pylint: disable=wrong-import-order
from distutils import errors                        # pylint: disable=wrong-import-order
import distutils.log                                # pylint: disable=wrong-import-order

# $set_env.py: COVERAGE_QUIETER - Set to remove some noise from test output.
if bool(int(os.getenv("COVERAGE_QUIETER", "0"))):
    # Distutils has its own mini-logging code, and it sets the level too high.
    # When I ask for --quiet when running tests, I don't want to see warnings.
    old_set_verbosity = distutils.log.set_verbosity
    def better_set_verbosity(v):
        """--quiet means no warnings!"""
        if v <= 0:
            distutils.log.set_threshold(distutils.log.ERROR)
        else:
            old_set_verbosity(v)
    distutils.log.set_verbosity = better_set_verbosity

# Get or massage our metadata.  We exec coverage/version.py so we can avoid
# importing the product code into setup.py.

# PYVERSIONS
classifiers = """\
Environment :: Console
Intended Audience :: Developers
License :: OSI Approved :: Apache Software License
Operating System :: OS Independent
Programming Language :: Python
Programming Language :: Python :: 3
Programming Language :: Python :: 3.7
Programming Language :: Python :: 3.8
Programming Language :: Python :: 3.9
Programming Language :: Python :: 3.10
Programming Language :: Python :: 3.11
Programming Language :: Python :: 3.12
Programming Language :: Python :: Implementation :: CPython
Programming Language :: Python :: Implementation :: PyPy
Topic :: Software Development :: Quality Assurance
Topic :: Software Development :: Testing
"""

cov_ver_py = os.path.join(os.path.split(__file__)[0], "coverage/version.py")
with open(cov_ver_py) as version_file:
    # __doc__ will be overwritten by version.py.
    doc = __doc__
    # Keep pylint happy.
    __version__ = __url__ = version_info = ""
    # Execute the code in version.py.
    exec(compile(version_file.read(), cov_ver_py, 'exec'))

with open("README.rst") as readme:
    long_description = readme.read().replace("https://coverage.readthedocs.io", __url__)

with open("CONTRIBUTORS.txt", "rb") as contributors:
    paras = contributors.read().split(b"\n\n")
    num_others = len(paras[-1].splitlines())
    num_others += 1                 # Count Gareth Rees, who is mentioned in the top paragraph.

classifier_list = classifiers.splitlines()

if version_info[3] == 'alpha':
    devstat = "3 - Alpha"
elif version_info[3] in ['beta', 'candidate']:
    devstat = "4 - Beta"
else:
    assert version_info[3] == 'final'
    devstat = "5 - Production/Stable"
classifier_list.append(f"Development Status :: {devstat}")

# Create the keyword arguments for setup()

setup_args = dict(
    name='coverage',
    version=__version__,

    packages=[
        'coverage',
    ],

    package_data={
        'coverage': [
            'htmlfiles/*.*',
            'fullcoverage/*.*',
        ]
    },

    entry_points={
        # Install a script as "coverage", and as "coverage3", and as
        # "coverage-3.7" (or whatever).
        'console_scripts': [
            'coverage = coverage.cmdline:main',
            'coverage%d = coverage.cmdline:main' % sys.version_info[:1],
            'coverage-%d.%d = coverage.cmdline:main' % sys.version_info[:2],
        ],
    },

    extras_require={
        # Enable pyproject.toml support.
        'toml': ['tomli; python_full_version<="3.11.0a6"'],
    },

    # We need to get HTML assets from our htmlfiles directory.
    zip_safe=False,

    author=f'Ned Batchelder and {num_others} others',
    author_email='ned@nedbatchelder.com',
    description=doc,
    long_description=long_description,
    long_description_content_type='text/x-rst',
    keywords='code coverage testing',
    license='Apache-2.0',
    classifiers=classifier_list,
    url="https://github.com/nedbat/coveragepy",
    project_urls={
        'Documentation': __url__,
        'Funding': (
            'https://tidelift.com/subscription/pkg/pypi-coverage' +
            '?utm_source=pypi-coverage&utm_medium=referral&utm_campaign=pypi'
        ),
        'Issues': 'https://github.com/nedbat/coveragepy/issues',
        'Mastodon': 'https://hachyderm.io/@nedbat',
        'Twitter': 'https://twitter.com/coveragepy',
    },
    python_requires=">=3.7",    # minimum of PYVERSIONS
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
        self.cause = sys.exc_info()[1]      # work around py 2/3 different syntax


class ve_build_ext(build_ext):
    """Build C extensions, but fail with a straightforward exception."""

    def run(self):
        """Wrap `run` with `BuildFailed`."""
        try:
            build_ext.run(self)
        except errors.DistutilsPlatformError as exc:
            raise BuildFailed() from exc

    def build_extension(self, ext):
        """Wrap `build_extension` with `BuildFailed`."""
        try:
            # Uncomment to test compile failure handling:
            #   raise errors.CCompilerError("OOPS")
            build_ext.build_extension(self, ext)
        except ext_errors as exc:
            raise BuildFailed() from exc
        except ValueError as err:
            # this can happen on Windows 64 bit, see Python issue 7511
            if "'path'" in str(err):    # works with both py 2/3
                raise BuildFailed() from err
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
        ext_modules=[
            Extension(
                "coverage.tracer",
                sources=[
                    "coverage/ctracer/datastack.c",
                    "coverage/ctracer/filedisp.c",
                    "coverage/ctracer/module.c",
                    "coverage/ctracer/tracer.c",
                ],
            ),
        ],
        cmdclass={
            'build_ext': ve_build_ext,
        },
    ))


def main():
    """Actually invoke setup() with the arguments we built above."""
    # For a variety of reasons, it might not be possible to install the C
    # extension.  Try it with, and if it fails, try it without.
    try:
        setup(**setup_args)
    except BuildFailed as exc:
        msg = "Couldn't install with extension module, trying without it..."
        exc_msg = f"{exc.__class__.__name__}: {exc.cause}"
        print(f"**\n** {msg}\n** {exc_msg}\n**")

        del setup_args['ext_modules']
        setup(**setup_args)

if __name__ == '__main__':
    main()
