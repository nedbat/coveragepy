# setup.py for coverage.

"""Code coverage testing for Python

Coverage.py is a Python package that measures code coverage during test execution.
It uses the code analysis tools and tracing hooks provided in the Python standard
library to determine which lines are executable, and which have been executed.
"""

classifiers = """
Development Status :: 5 - Production/Stable
Environment :: Console
Intended Audience :: Developers
License :: OSI Approved :: BSD License
Operating System :: OS Independent
Programming Language :: Python
Topic :: Software Development :: Quality Assurance
Topic :: Software Development :: Testing
"""

from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages
from distutils.core import Extension

from coverage import __version__

doclines = __doc__.split("\n")

setup(
    name = 'coverage',
    version = __version__,

    packages = [
        'coverage',
        ],

    entry_points={
        'console_scripts': [
            'coverage = coverage:main',
        ]
    },
    zip_safe = True,    # __file__ appears in the source, but doesn't break zippy-ness.

    ext_modules = [
        Extension("coverage.tracer", sources=["coverage/tracer.c"])
        ],
    
    author = 'Ned Batchelder',
    author_email = 'ned@nedbatchelder.com',
    description = doclines[0],
    long_description = "\n".join(doclines[2:]),
    keywords = 'code coverage testing',
    license = 'BSD',
    classifiers = filter(None, classifiers.split("\n")),
    url = 'http://nedbatchelder.com/code/modules/coverage.html',
    download_url = 'http://nedbatchelder.com/code/modules/coverage-%s.tar.gz' % __version__,
)
