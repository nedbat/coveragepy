# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Sqlite coverage data."""

import os
import sqlite3

from coverage.backward import iitems
from coverage.misc import CoverageException, file_be_gone


SCHEMA = """
create table schema (
    version integer
);

insert into schema (version) values (1);

create table meta (
    name text,
    value text,
    unique(name)
);

create table file (
    id integer primary key,
    path text,
    tracer text,
    unique(path)
);

create table line (
    file_id integer,
    lineno integer,
    unique(file_id, lineno)
);

create table arc (
    file_id integer,
    fromno integer,
    tono integer,
    unique(file_id, fromno, tono)
);
"""

APP_ID = 0x0c07ea6e     # Kind of looks like "coverage"


class CoverageSqliteData(object):
    def __init__(self, basename=None, warn=None, debug=None):
        self.filename = os.path.abspath(basename or ".coverage")
        self._warn = warn
        self._debug = debug

        self._file_map = {}
        self._db = None
        self._have_read = False

    def _reset(self):
        self._file_map = {}
        if self._db is not None:
            self._db.close()
        self._db = None

    def _connect(self):
        if self._db is None:
            if not os.path.exists(self.filename):
                if self._debug and self._debug.should('dataio'):
                    self._debug.write("Creating data file %r" % (self.filename,))
                self._db = Sqlite(self.filename, self._debug)
                with self._db:
                    self._db.execute("pragma application_id = {}".format(APP_ID))
                    for stmt in SCHEMA.split(';'):
                        stmt = stmt.strip()
                        if stmt:
                            self._db.execute(stmt)
            else:
                self._db = Sqlite(self.filename, self._debug)
                with self._db:
                    for app_id, in self._db.execute("pragma application_id"):
                        app_id = int(app_id)
                        if app_id != APP_ID:
                            raise Exception("Doesn't look like a coverage data file: 0x{:08x} != 0x{:08x}".format(app_id, APP_ID))
            for path, id in self._db.execute("select path, id from file"):
                self._file_map[path] = id
        return self._db

    def _file_id(self, filename):
        self._start_writing()
        if filename not in self._file_map:
            with self._connect() as con:
                cur = con.execute("insert into file (path) values (?)", (filename,))
                self._file_map[filename] = cur.lastrowid
        return self._file_map[filename]

    def add_lines(self, line_data):
        """Add measured line data.

        `line_data` is a dictionary mapping file names to dictionaries::

            { filename: { lineno: None, ... }, ...}

        """
        self._start_writing()
        with self._connect() as con:
            for filename, linenos in iitems(line_data):
                file_id = self._file_id(filename)
                data = [(file_id, lineno) for lineno in linenos]
                con.executemany(
                    "insert or ignore into line (file_id, lineno) values (?, ?)",
                    data,
                )

    def add_file_tracers(self, file_tracers):
        """Add per-file plugin information.

        `file_tracers` is { filename: plugin_name, ... }

        """
        self._start_writing()
        with self._connect() as con:
            for filename, tracer in iitems(file_tracers):
                con.execute(
                    "insert into file (path, tracer) values (?, ?) on duplicate key update",
                    (filename, tracer),
                )

    def erase(self, parallel=False):
        """Erase the data in this object.

        If `parallel` is true, then also deletes data files created from the
        basename by parallel-mode.

        """
        self._reset()
        if self._debug and self._debug.should('dataio'):
            self._debug.write("Erasing data file %r" % (self.filename,))
        file_be_gone(self.filename)
        if parallel:
            data_dir, local = os.path.split(self.filename)
            localdot = local + '.*'
            pattern = os.path.join(os.path.abspath(data_dir), localdot)
            for filename in glob.glob(pattern):
                if self._debug and self._debug.should('dataio'):
                    self._debug.write("Erasing parallel data file %r" % (filename,))
                file_be_gone(filename)

    def read(self):
        self._connect()     # TODO: doesn't look right
        self._have_read = True

    def write(self, suffix=None):
        """Write the collected coverage data to a file."""
        pass

    def _start_writing(self):
        if not self._have_read:
            self.erase()
        self._have_read = True

    def has_arcs(self):
        return False    # TODO!

    def measured_files(self):
        """A list of all files that had been measured."""
        return list(self._file_map)

    def file_tracer(self, filename):
        """Get the plugin name of the file tracer for a file.

        Returns the name of the plugin that handles this file.  If the file was
        measured, but didn't use a plugin, then "" is returned.  If the file
        was not measured, then None is returned.

        """
        return ""    # TODO

    def lines(self, filename):
        with self._connect() as con:
            file_id = self._file_id(filename)
            return [lineno for lineno, in con.execute("select lineno from line where file_id = ?", (file_id,))]


class Sqlite(object):
    def __init__(self, filename, debug):
        self.debug = debug if (debug and debug.should('sql')) else None
        if self.debug:
            self.debug.write("Connecting to {!r}".format(filename))
        self.con = sqlite3.connect(filename)

        # This pragma makes writing faster. It disables rollbacks, but we never need them.
        self.con.execute("pragma journal_mode=off")
        # This pragma makes writing faster.
        self.con.execute("pragma synchronous=off")

    def close(self):
        self.con.close()

    def __enter__(self):
        self.con.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return self.con.__exit__(exc_type, exc_value, traceback)

    def execute(self, sql, parameters=()):
        if self.debug:
            tail = " with {!r}".format(parameters) if parameters else ""
            self.debug.write("Executing {!r}{}".format(sql, tail))
        return self.con.execute(sql, parameters)

    def executemany(self, sql, data):
        if self.debug:
            self.debug.write("Executing many {!r}".format(sql))
        return self.con.executemany(sql, data)
