# setup.py for coverage.

"""Code coverage measurement for Python

Coverage measures code coverage, typically during test execution.  It uses the
code analysis tools and tracing hooks provided in the Python standard library
to determine which lines are executable, and which have been executed.
"""

classifiers = """
Environment :: Console
Intended Audience :: Developers
License :: OSI Approved :: BSD License
Operating System :: OS Independent
Programming Language :: Python
Topic :: Software Development :: Quality Assurance
Topic :: Software Development :: Testing
"""

# Pull in the tools we need.

from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages
from distutils.core import Extension

# Get or massage our metadata.

from coverage import __version__

doclines = __doc__.split("\n")

classifier_list = filter(None, classifiers.split("\n"))

if 'a' in __version__:
    devstat = "3 - Alpha"
elif 'b' in __version__:
    devstat = "4 - Beta"
else:
    devstat = "5 - Production/Stable"
classifier_list.append("Development Status :: " + devstat)

# Set it up!

setup(
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

    entry_points={
        'console_scripts': [
            'coverage = coverage:main',
        ]
    },
    ext_modules = [
        Extension("coverage.tracer", sources=["coverage/tracer.c"])
        ],
    
    zip_safe = False,    # we need to get HTML assets from our htmlfiles dir.

    author = 'Ned Batchelder',
    author_email = 'ned@nedbatchelder.com',
    description = doclines[0],
    long_description = "\n".join(doclines[2:]),
    keywords = 'code coverage testing',
    license = 'BSD',
    classifiers = classifier_list,
    url = 'http://nedbatchelder.com/code/modules/coverage.html',
    # download_url = 'http://nedbatchelder.com/code/modules/coverage-%s.tar.gz' % __version__,
)
