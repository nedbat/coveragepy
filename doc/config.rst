.. _config:

===================
Configuration files
===================

:history: 20100223T201600, new for 3.3
:history: 20100725T211700, updated for 3.4.


Coverage.py options can be specified in a configuration file.  This makes it
easier to re-run coverage with consistent settings, and also allows for
specification of options that are otherwise only available in the
:ref:`API <api>`.

Configuration files also make it easier to get coverage testing of spawned
sub-processes.  See :ref:`subprocess` for more details.



Syntax
------

A coverage.py configuration file is in classic .ini file format: sections are
introduced by a ``[section]`` header, and contain ``name = value`` entries.
Lines beginning with ``#`` or ``;`` are ignored as comments.

Strings don't need quotes. Multi-strings can be created by indenting values on
multiple lines.

Boolean values can be specified as ``on``, ``off``, ``true``, ``false``, ``1``,
or ``0`` and are case-insensitive.

Many sections and values correspond roughly to commands and options in
the :ref:`command-line interface <cmd>`.

Here's a sample configuration file::

    # .coveragerc to control coverage.py
    [run]
    branch = True

    [report]
    # Regexes for lines to exclude from consideration
    exclude_lines =
        # Have to re-enable the standard pragma
        pragma: no cover

        # Don't complain about missing debug-only code:
        def __repr__
        if self\.debug

        # Don't complain if tests don't hit defensive assertion code:
        raise AssertionError
        raise NotImplementedError

        # Don't complain if non-runnable code isn't run:
        if 0:
        if __name__ == .__main__.:

    ignore_errors = True

    [html]
    directory = coverage_html_report


[run]
-----

These values are generally used when running product code, though some apply
to more than one command.

``branch`` (boolean, default False): whether to measure
:ref:`branch coverage <branch>` in addition to statement coverage.

``cover_pylib`` (boolean, default False): whether to measure the Python
standard library.

``data_file`` (string, default ".coverage"): the name of the data file to use
for storing or reporting coverage.

``include`` (multi-string): a list of filename patterns, the files to include
in measurement or reporting.  See :ref:`source` for details.

``omit`` (multi-string): a list of filename patterns, the files to leave out
of measurement or reporting.  See :ref:`source` for details.

``parallel`` (boolean, default False): append the machine name, process
id and random number to the data file name to simplify collecting data from
many processes.  See :ref:`cmd_combining` for more information.

``source`` (multi-string): a list of packages or directories, the source to
measure during execution.  See :ref:`source` for details.

``timid`` (boolean, default False): use a simpler but slower trace method.
Try this if you get seemingly impossible results.


[report]
--------

Values common to many kinds of reporting.

``exclude_lines`` (multi-string): a list of regular expressions.  Any line of
your source code that matches one of these regexes is excluded from being
reported as missing.  More details are in :ref:`excluding`.  If you use this
option, you are replacing all the exclude regexes, so you'll need to also
supply the "pragma: no cover" regex if you still want to use it.

``ignore_errors`` (boolean, default False): ignore source code that can't be
found.

``include`` (multi-string): a list of filename patterns, the files to include
in reporting.  See :ref:`source` for details.

``omit`` (multi-string): a list of filename patterns, the files to leave out
of reporting.  See :ref:`source` for details.


[html]
------

Values particular to HTML reporting.  The values in the ``[report]`` section
also apply to HTML output.

``directory`` (string, default "htmlcov"): where to write the HTML report files.


[xml]
-----

Values particular to XML reporting.  The values in the ``[report]`` section
also apply to XML output.

``output`` (string, default "coverage.xml"): where to write the XML report.
