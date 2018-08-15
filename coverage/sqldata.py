# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Sqlite coverage data."""

# TODO: get rid of skip_unless_data_storage_is_json
# TODO: check the schema
# TODO: factor out dataop debugging to a wrapper class?
# TODO: make sure all dataop debugging is in place somehow
# TODO: should writes be batched?
# TODO: settle the os.fork question

import glob
import os
import sqlite3
import struct

from coverage.backward import iitems
from coverage.data import filename_suffix
from coverage.debug import SimpleRepr
from coverage.files import PathAliases
from coverage.misc import CoverageException, file_be_gone


SCHEMA = """
create table schema (
    version integer
);

insert into schema (version) values (1);

create table meta (
    has_lines boolean,
    has_arcs boolean
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

APP_ID = 0xc07e8a6e         # "coverage", kind of.

def unsigned_to_signed(val):
    return struct.unpack('>i', struct.pack('>I', val))[0]

def signed_to_unsigned(val):
    return struct.unpack('>I', struct.pack('>i', val))[0]

class CoverageSqliteData(SimpleRepr):
    def __init__(self, basename=None, suffix=None, warn=None, debug=None):
        self.filename = os.path.abspath(basename or ".coverage")
        suffix = filename_suffix(suffix)
        if suffix:
            self.filename += "." + suffix
        self._warn = warn
        self._debug = debug

        self._file_map = {}
        self._db = None
        # Are we in sync with the data file?
        self._have_read = False

        self._has_lines = False
        self._has_arcs = False

    def _reset(self):
        self._file_map = {}
        if self._db is not None:
            self._db.close()
        self._db = None
        self._have_read = False

    def _create_db(self):
        if self._debug and self._debug.should('dataio'):
            self._debug.write("Creating data file {!r}".format(self.filename))
        self._db = Sqlite(self.filename, self._debug)
        with self._db:
            self._db.execute("pragma application_id = {}".format(unsigned_to_signed(APP_ID)))
            for stmt in SCHEMA.split(';'):
                stmt = stmt.strip()
                if stmt:
                    self._db.execute(stmt)
            self._db.execute(
                "insert into meta (has_lines, has_arcs) values (?, ?)",
                (self._has_lines, self._has_arcs)
            )

    def _open_db(self):
        if self._debug and self._debug.should('dataio'):
            self._debug.write("Opening data file {!r}".format(self.filename))
        self._db = Sqlite(self.filename, self._debug)
        with self._db:
            for app_id, in self._db.execute("pragma application_id"):
                app_id = signed_to_unsigned(int(app_id))
                if app_id != APP_ID:
                    raise CoverageException(
                        "Couldn't use {!r}: wrong application_id: "
                        "0x{:08x} != 0x{:08x}".format(self.filename, app_id, APP_ID)
                    )
        for row in self._db.execute("select has_lines, has_arcs from meta"):
            self._has_lines, self._has_arcs = row

        for path, id in self._db.execute("select path, id from file"):
            self._file_map[path] = id

    def _connect(self):
        if self._db is None:
            if os.path.exists(self.filename):
                self._open_db()
            else:
                self._create_db()
            self._have_read = True
        return self._db

    def __nonzero__(self):
        try:
            with self._connect() as con:
                if self.has_arcs():
                    rows = con.execute("select * from arc limit 1")
                else:
                    rows = con.execute("select * from line limit 1")
                return bool(list(rows))
        except CoverageException:
            return False

    __bool__ = __nonzero__

    def _file_id(self, filename, add=False):
        """Get the file id for `filename`.

        If filename is not in the database yet, add if it `add` is True.
        If `add` is not True, return None.
        """
        if filename not in self._file_map:
            if add:
                self._start_writing()
                with self._connect() as con:
                    cur = con.execute("insert into file (path) values (?)", (filename,))
                    self._file_map[filename] = cur.lastrowid
        return self._file_map.get(filename)

    def add_lines(self, line_data):
        """Add measured line data.

        `line_data` is a dictionary mapping file names to dictionaries::

            { filename: { lineno: None, ... }, ...}

        """
        if self._debug and self._debug.should('dataop'):
            self._debug.write("Adding lines: %d files, %d lines total" % (
                len(line_data), sum(len(lines) for lines in line_data.values())
            ))
        self._start_writing()
        self._choose_lines_or_arcs(lines=True)
        with self._connect() as con:
            for filename, linenos in iitems(line_data):
                file_id = self._file_id(filename, add=True)
                data = [(file_id, lineno) for lineno in linenos]
                con.executemany(
                    "insert or ignore into line (file_id, lineno) values (?, ?)",
                    data,
                )

    def add_arcs(self, arc_data):
        """Add measured arc data.

        `arc_data` is a dictionary mapping file names to dictionaries::

            { filename: { (l1,l2): None, ... }, ...}

        """
        if self._debug and self._debug.should('dataop'):
            self._debug.write("Adding arcs: %d files, %d arcs total" % (
                len(arc_data), sum(len(arcs) for arcs in arc_data.values())
            ))
        self._start_writing()
        self._choose_lines_or_arcs(arcs=True)
        with self._connect() as con:
            for filename, arcs in iitems(arc_data):
                file_id = self._file_id(filename, add=True)
                data = [(file_id, fromno, tono) for fromno, tono in arcs]
                con.executemany(
                    "insert or ignore into arc (file_id, fromno, tono) values (?, ?, ?)",
                    data,
                )

    def _choose_lines_or_arcs(self, lines=False, arcs=False):
        if lines and self._has_arcs:
            raise CoverageException("Can't add lines to existing arc data")
        if arcs and self._has_lines:
            raise CoverageException("Can't add arcs to existing line data")
        if not self._has_arcs and not self._has_lines:
            self._has_lines = lines
            self._has_arcs = arcs
            with self._connect() as con:
                con.execute("update meta set has_lines = ?, has_arcs = ?", (lines, arcs))

    def add_file_tracers(self, file_tracers):
        """Add per-file plugin information.

        `file_tracers` is { filename: plugin_name, ... }

        """
        self._start_writing()
        with self._connect() as con:
            for filename, plugin_name in iitems(file_tracers):
                file_id = self._file_id(filename)
                if file_id is None:
                    raise CoverageException(
                        "Can't add file tracer data for unmeasured file '%s'" % (filename,)
                    )

                cur = con.execute("select tracer from file where id = ?", (file_id,))
                [existing_plugin] = cur.fetchone()
                if existing_plugin is not None and existing_plugin != plugin_name:
                    raise CoverageException(
                        "Conflicting file tracer name for '%s': %r vs %r" % (
                            filename, existing_plugin, plugin_name,
                        )
                    )

                con.execute(
                    "update file set tracer = ? where path = ?",
                    (plugin_name, filename)
                )

    def touch_file(self, filename, plugin_name=""):
        """Ensure that `filename` appears in the data, empty if needed.

        `plugin_name` is the name of the plugin resposible for this file. It is used
        to associate the right filereporter, etc.
        """
        if self._debug and self._debug.should('dataop'):
            self._debug.write("Touching %r" % (filename,))
        if not self._has_arcs and not self._has_lines:
            raise CoverageException("Can't touch files in an empty CoverageSqliteData")

        self._file_id(filename, add=True)
        if plugin_name:
            # Set the tracer for this file
            self.add_file_tracers({filename: plugin_name})

    def update(self, other_data, aliases=None):
        if self._has_lines and other_data._has_arcs:
            raise CoverageException("Can't combine arc data with line data")
        if self._has_arcs and other_data._has_lines:
            raise CoverageException("Can't combine line data with arc data")

        aliases = aliases or PathAliases()

        # lines
        if other_data._has_lines:
            for filename in other_data.measured_files():
                lines = set(other_data.lines(filename))
                filename = aliases.map(filename)
                lines.update(self.lines(filename) or ())
                self.add_lines({filename: lines})

        # arcs
        if other_data._has_arcs:
            for filename in other_data.measured_files():
                arcs = set(other_data.arcs(filename))
                filename = aliases.map(filename)
                arcs.update(self.arcs(filename) or ())
                self.add_arcs({filename: arcs})

        # file_tracers
        for filename in other_data.measured_files():
            other_plugin = other_data.file_tracer(filename)
            filename = aliases.map(filename)
            self.add_file_tracers({filename: other_plugin})


    def erase(self, parallel=False):
        """Erase the data in this object.

        If `parallel` is true, then also deletes data files created from the
        basename by parallel-mode.

        """
        self._reset()
        if self._debug and self._debug.should('dataio'):
            self._debug.write("Erasing data file {!r}".format(self.filename))
        file_be_gone(self.filename)
        if parallel:
            data_dir, local = os.path.split(self.filename)
            localdot = local + '.*'
            pattern = os.path.join(os.path.abspath(data_dir), localdot)
            for filename in glob.glob(pattern):
                if self._debug and self._debug.should('dataio'):
                    self._debug.write("Erasing parallel data file {!r}".format(filename))
                file_be_gone(filename)

    def read(self):
        self._connect()     # TODO: doesn't look right
        self._have_read = True

    def write(self):
        """Write the collected coverage data to a file."""
        pass

    def _start_writing(self):
        if not self._have_read:
            self.erase()
        self._have_read = True

    def has_arcs(self):
        return self._has_arcs

    def measured_files(self):
        """A list of all files that had been measured."""
        return list(self._file_map)

    def file_tracer(self, filename):
        """Get the plugin name of the file tracer for a file.

        Returns the name of the plugin that handles this file.  If the file was
        measured, but didn't use a plugin, then "" is returned.  If the file
        was not measured, then None is returned.

        """
        with self._connect() as con:
            for tracer, in con.execute("select tracer from file where path = ?", (filename,)):
                return tracer or ""
        return None

    def lines(self, filename):
        if self.has_arcs():
            arcs = self.arcs(filename)
            if arcs is not None:
                import itertools
                all_lines = itertools.chain.from_iterable(arcs)
                return list(set(l for l in all_lines if l > 0))

        with self._connect() as con:
            file_id = self._file_id(filename)
            if file_id is None:
                return None
            else:
                linenos = con.execute("select lineno from line where file_id = ?", (file_id,))
                return [lineno for lineno, in linenos]

    def arcs(self, filename):
        with self._connect() as con:
            file_id = self._file_id(filename)
            if file_id is None:
                return None
            else:
                arcs = con.execute("select fromno, tono from arc where file_id = ?", (file_id,))
                return [pair for pair in arcs]

    def run_infos(self):
        return []   # TODO


class Sqlite(SimpleRepr):
    def __init__(self, filename, debug):
        self.debug = debug if (debug and debug.should('sql')) else None
        if self.debug:
            self.debug.write("Connecting to {!r}".format(filename))
        self.filename = filename
        self.con = sqlite3.connect(self.filename)

        # This pragma makes writing faster. It disables rollbacks, but we never need them.
        self.execute("pragma journal_mode=off")
        # This pragma makes writing faster.
        self.execute("pragma synchronous=off")

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
        try:
            return self.con.execute(sql, parameters)
        except sqlite3.Error as exc:
            raise CoverageException("Couldn't use data file {!r}: {}".format(self.filename, exc))

    def executemany(self, sql, data):
        if self.debug:
            self.debug.write("Executing many {!r} with {} rows".format(sql, len(data)))
        return self.con.executemany(sql, data)
