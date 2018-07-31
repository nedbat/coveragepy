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

def _create_db(filename, schema):
    con = sqlite3.connect(filename)
    with con:
        for stmt in schema.split(';'):
            con.execute(stmt.strip())
    con.close()


class CoverageDataSqlite(object):
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
                _create_db(self.filename, SCHEMA)
            self._db = sqlite3.connect(self.filename)
            for path, id in self._db.execute("select path, id from file"):
                self._file_map[path] = id
        return self._db

    def _file_id(self, filename):
        self._start_writing()
        if filename not in self._file_map:
            with self._connect() as con:
                cur = con.cursor()
                cur.execute("insert into file (path) values (?)", (filename,))
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
                for lineno in linenos:
                    con.execute(
                        "insert or ignore into line (file_id, lineno) values (?, ?)",
                        (file_id, lineno),
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
        self._connect()
        return list(self._file_map)

    def file_tracer(self, filename):
        """Get the plugin name of the file tracer for a file.

        Returns the name of the plugin that handles this file.  If the file was
        measured, but didn't use a plugin, then "" is returned.  If the file
        was not measured, then None is returned.

        """
        with self._connect() as con:
            pass
