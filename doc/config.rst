.. _config:

===================
Configuration files
===================

:history: 20100223T201600, new for 3.3

Coverage.py options can be specified in a configuration file.  This makes it
easier to re-run coverage with consistent settings, and also allows for
specification of options that are otherwise only available in the
:ref:`API <api>`.

Configuration files also make it easier to get coverage testing of spawned
sub-processes.  See :ref:`Subprocess measurement <subprocess>` for more details.



Syntax
------

A coverage.py configuration file is in classic .ini file format: sections are
introduced by a ``[section]`` header, and contain ``name = value`` entries.
Lines beginning with ``#`` or ``;`` are ignored as comments.

Multi-line entries can be created by indenting values on multiple lines.

Boolean values can be specified as ``on``, ``off``, ``true``, ``false``, ``1``,
or ``0``.

Many sections and values correspond roughly to commands and options in the
command-line interface.


[run]
-----

These values are generally used when running product code, though some apply
to more than one command.

``branch`` (boolean): whether to measure :ref:`branch coverage <branch>`.

``cover_pylib`` (boolean): whether to measure the Python standard library.

``data_file`` (string): the name of the data file to use for storing or
reporting coverage.

``parallel`` (boolean):

``timid`` (boolean):


[report]
--------

Values common to many kinds of reporting.

``exclude_lines`` (multi-string):

``ignore_errors`` (boolean):

``omit`` (multi-string):


[html]
------

Values particular to HTML reporting.

``directory`` (string):


[xml]
-----

Values particular to XML reporting.

``output`` (string):

