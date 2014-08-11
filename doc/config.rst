.. _config:

===================
Configuration files
===================

:history: 20100223T201600, new for 3.3
:history: 20100725T211700, updated for 3.4.
:history: 20100824T092900, added ``precision``.
:history: 20110604T184400, updated for 3.5.
:history: 20110827T212700, updated for 3.5.1
:history: 20130926T222300, updated for 3.6.1


Coverage.py options can be specified in a configuration file.  This makes it
easier to re-run coverage with consistent settings, and also allows for
specification of options that are otherwise only available in the
:ref:`API <api>`.

Configuration files also make it easier to get coverage testing of spawned
sub-processes.  See :ref:`subprocess` for more details.

The default name for configuration files is ``.coveragerc``, in the same
directory coverage.py is being run in.  Most of the settings in the
configuration file are tied to your source code and how it should be measured,
so it should be stored with your source, and checked into source control,
rather than put in your home directory.


Syntax
------

A coverage.py configuration file is in classic .ini file format: sections are
introduced by a ``[section]`` header, and contain ``name = value`` entries.
Lines beginning with ``#`` or ``;`` are ignored as comments.

Strings don't need quotes. Multi-valued strings can be created by indenting
values on multiple lines.

Boolean values can be specified as ``on``, ``off``, ``true``, ``false``, ``1``,
or ``0`` and are case-insensitive.

Environment variables can be substituted in by using dollar signs: ``$WORD``
or ``${WORD}`` will be replaced with the value of ``WORD`` in the environment.
A dollar sign can be inserted with ``$$``.  Missing environment variables
will result in empty strings with no error.

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

``debug`` (multi-string): a list of debug options.  See :ref:`the run
--debug option <cmd_run_debug>` for details.

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


.. _config_paths:

[paths]
-------

The entries in this section are lists of file paths that should be considered
equivalent when combining data from different machines::

    [paths]
    source =
        src/
        /jenkins/build/*/src
        c:\myproj\src

The names of the entries are ignored, you may choose any name that you like.
The value is a lists of strings.  When combining data with the ``combine``
command, two file paths will be combined if they start with paths from the same
list.

The first value must be an actual file path on the machine where the reporting
will happen, so that source code can be found.  The other values can be file
patterns to match against the paths of collected data, or they can be absolute
or relative file paths on the current machine.

See :ref:`cmd_combining` for more information.


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

``partial_branches`` (multi-string): a list of regular expressions.  Any line
of code that matches one of these regexes is excused from being reported as
a partial branch.  More details are in :ref:`branch`.  If you use this option,
you are replacing all the partial branch regexes so you'll need to also
supply the "pragma: no branch" regex if you still want to use it.

``precision`` (integer): the number of digits after the decimal point to
display for reported coverage percentages.  The default is 0, displaying for
example "87%".  A value of 2 will display percentages like "87.32%".

``show_missing`` (boolean, default False): when running a summary report, show
missing lines.  See :ref:`cmd_summary` for more information.


.. _config_html:

[html]
------

Values particular to HTML reporting.  The values in the ``[report]`` section
also apply to HTML output, where appropriate.

``directory`` (string, default "htmlcov"): where to write the HTML report files.

``extra_css`` (string): the path to a file of CSS to apply to the HTML report.
The file will be copied into the HTML output directory.  Don't name it
"style.css".  This CSS is in addition to the CSS normally used, though you can
overwrite as many of the rules as you like.

``title`` (string, default "Coverage report"): the title to use for the report.
Note this is text, not HTML.


[xml]
-----

Values particular to XML reporting.  The values in the ``[report]`` section
also apply to XML output, where appropriate.

``output`` (string, default "coverage.xml"): where to write the XML report.
