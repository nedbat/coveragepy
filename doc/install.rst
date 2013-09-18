.. _install:

============
Installation
============

:history: 20100725T225600, new for 3.4.
:history: 20100820T151500, updated for 3.4b1.
:history: 20100906T134800, updated for 3.4b2.
:history: 20110604T213400, updated for 3.5b1.
:history: 20110629T082400, updated for 3.5.
:history: 20110923T081900, updated for 3.5.1.
:history: 20120429T162500, updated for 3.5.2b1.
:history: 20120503T234000, updated for 3.5.2.
:history: 20120929T093600, updated for 3.5.3.
:history: 20121117T095000, Now setuptools is a pre-req.
:history: 20121128T203000, updated for 3.6b1.
:history: 20121223T180800, updated for 3.6b2.
:history: 20121229T112400, updated for 3.6b3.
:history: 20130105T174400, updated for 3.6.


.. highlight:: console
.. _coverage_pypi: http://pypi.python.org/pypi/coverage
.. _setuptools: http://pypi.python.org/pypi/setuptools
.. _Distribute: http://packages.python.org/distribute/


Installing coverage.py is done in the usual ways. You must have `setuptools`_
or `Distribute`_ installed already, and then you:

#.  Download the appropriate kit from the
    `coverage page on the Python Package Index`__.

#.  Run ``python setup.py install``.

or, use::

    $ pip install coverage

or even::

    $ easy_install coverage

.. __: coverage_pypi_


Installing from source
----------------------

Coverage.py includes a C extension for speed. If you are installing from
source, you may need to install the python-dev support files, for example
with::

    $ sudo apt-get install python-dev


Installing on Windows
---------------------

For Windows, kits are provided on the `PyPI page`__ for different versions of
Python and different CPU architectures. These kits require that `setuptools`_
be installed as a pre-requisite, but otherwise are self-contained.  They have
the C extension pre-compiled so there's no need to worry about compilers.

.. __: coverage_pypi_


Checking the installation
-------------------------

If all went well, you should be able to open a command prompt, and see coverage
installed properly::

    $ coverage --version
    Coverage.py, version 3.6.  http://nedbatchelder.com/code/coverage

You can also invoke coverage as a module::

    $ python -m coverage --version
    Coverage.py, version 3.6.  http://nedbatchelder.com/code/coverage
