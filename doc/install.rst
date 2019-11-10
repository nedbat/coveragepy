.. Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
.. For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

.. _install:

============
Installation
============

.. highlight:: console

.. _coverage_pypi: https://pypi.org/project/coverage/
.. _setuptools: https://pypi.org/project/setuptools/


You can install coverage.py in the usual ways. The simplest way is with pip::

    $ pip install coverage

.. ifconfig:: prerelease

    To install a pre-release version, you will need to specify ``--pre``::

        $ pip install --pre coverage


.. _install_extension:

C Extension
-----------

Coverage.py includes a C extension for speed. It is strongly recommended to use
this extension: it is much faster, and is needed to support a number of
coverage.py features.  Most of the time, the C extension will be installed
without any special action on your part.

If you are installing on Linux, you may need to install the python-dev and gcc
support files before installing coverage via pip.  The exact commands depend on
which package manager you use, which Python version you are using, and the
names of the packages for your distribution.  For example::

    $ sudo apt-get install python-dev gcc
    $ sudo yum install python-devel gcc

    $ sudo apt-get install python3-dev gcc
    $ sudo yum install python3-devel gcc

You can determine if you are using the extension by looking at the output of
``coverage --version``::

    $ coverage --version
    Coverage.py, version |release| with C extension
    Documentation at https://coverage.readthedocs.io

The first line will either say "with C extension," or "without C extension."

A few features of coverage.py aren't supported without the C extension, such
as concurrency and plugins.


Installing on Windows
---------------------

For Windows, kits are provided on the `PyPI page`__ for different versions of
Python and different CPU architectures. These kits require that `setuptools`_
be installed as a pre-requisite, but otherwise are self-contained.  They have
the C extension pre-compiled so there's no need to worry about compilers.

.. __: coverage_pypi_


Checking the installation
-------------------------

If all went well, you should be able to open a command prompt, and see
coverage.py installed properly:

.. In the output below, the URL should actually have the release in it for
   pre-release, but Sphinx couldn't make a URL like that, so whatever.

.. parsed-literal::

    $ coverage --version
    Coverage.py, version |release| with C extension
    Documentation at https://coverage.readthedocs.io

You can also invoke coverage.py as a module:

.. parsed-literal::

    $ python -m coverage --version
    Coverage.py, version |release| with C extension
    Documentation at https://coverage.readthedocs.io
