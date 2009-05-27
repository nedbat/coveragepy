.. _api:

============
Coverage API
============

The API to coverage.py is very simple, contained in a single module called
coverage containing a single class, also called coverage::
    
    import coverage

    cov = coverage.coverage()
    
Methods on the coverage object correspond to operations available in the
command line interface.  For example, a simple use would be::

    import coverage
    
    cov = coverage.coverage()
    cov.start()
    
    # .. run your code ..
    
    cov.stop()
    cov.save()


The coverage module
-------------------

.. module:: coverage

.. autoclass:: coverage
    :members: 
