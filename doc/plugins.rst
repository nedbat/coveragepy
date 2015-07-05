.. _plugins:

=======
Plugins
=======

.. :history: 20150124T143000, new page.

Coverage.py's behavior can be extended by writing plugins.  A plugin is a
separately installed Python class that you register in your .coveragerc.
Plugins can be used to implement coverage measurement for non-Python files.

Using plugins
-------------

To use a coverage.py plugin, you install it, and configure it.  For this
example, let's say you want to use one called fred_plugin.

#. Install the plugin as you would any other Python package::

    pip install fred_plugin

#. Configure coverage.py to use the plugin.  You do this by editing (or
   creating) your .coveragerc file, as described in :ref:`config`.  The
   ``plugins`` setting indicates your plugin::

    [run]
    plugins =
        fred_plugin

#. If the plugin needs its own configuration, you can add those settings in
   the .coveragerc file in a section named for the plugin::

    [fred_plugin]
    option1 = True
    option2 = abc.foo

   Check the documentation for the plugin to see if it takes any options, and
   what they are.

#. Run your tests as you usually would.


Plugin API
----------

.. module:: coverage.plugin

.. autoclass:: CoveragePlugin
    :members:

.. autoclass:: FileTracer
    :members:

.. autoclass:: FileReporter
    :members:
