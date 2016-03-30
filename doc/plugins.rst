.. Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
.. For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

.. _plugins:

=======
Plugins
=======

.. :history: 20150124T143000, new page.
.. :history: 20150802T174600, updated for 4.0b1


Coverage.py's behavior can be extended with third-party plugins.  A plugin is a
separately installed Python class that you register in your .coveragerc.
Plugins can be used to implement coverage measurement for non-Python files.

Plugins are only supported with the :ref:`C extension <install_extension>`,
which must be installed for plugins to work.

Information about using plugins is on this page.  To write a plugin, see
:ref:`api_plugin`.

.. versionadded:: 4.0


Using plugins
-------------

To use a coverage.py plugin, you install it, and configure it.  For this
example, let's say there's a Python package called ``something`` that provides a
coverage.py plugin called ``something.plugin``.

#. Install the plugin's package as you would any other Python package::

    pip install something

#. Configure coverage.py to use the plugin.  You do this by editing (or
   creating) your .coveragerc file, as described in :ref:`config`.  The
   ``plugins`` setting indicates your plugin.  It's a list of importable module
   names of plugins::

    [run]
    plugins =
        something.plugin

#. If the plugin needs its own configuration, you can add those settings in
   the .coveragerc file in a section named for the plugin::

    [something.plugin]
    option1 = True
    option2 = abc.foo

   Check the documentation for the plugin to see if it takes any options, and
   what they are.

#. Run your tests with coverage.py as you usually would.  If you get a message
   like "Plugin file tracers (something.plugin) aren't supported with
   PyTracer," then you don't have the :ref:`C extension <install_extension>`
   installed.


Available plugins
-----------------

Some coverage.py plugins you might find useful:

* `Django template coverage.py plugin`__: for measuring coverage in Django
  templates.

  .. __: https://pypi.python.org/pypi/django_coverage_plugin

* `Mako template coverage plugin`__: for measuring coverage in Mako templates.
  Doesn't work yet, probably needs some changes in Mako itself.

  .. __: https://bitbucket.org/ned/coverage-mako-plugin
