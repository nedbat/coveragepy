# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Sqlite coverage data."""

# TODO: get sys_info for data class, so we can see sqlite version etc
# TODO: get rid of skip_unless_data_storage_is
# TODO: get rid of "JSON message" and "SQL message" in the tests
# TODO: factor out dataop debugging to a wrapper class?
# TODO: make sure all dataop debugging is in place somehow
# TODO: should writes be batched?
# TODO: run_info

import glob
import itertools
import os
import sqlite3
import sys

from coverage.backward import get_thread_id, iitems
from coverage.data import filename_suffix
from coverage.debug import NoDebugging, SimpleReprMixin
from coverage.files import PathAliases
from coverage.misc import CoverageException, file_be_gone


# Schema versions:
# 1: Released in 5.0a2
# 2: Added contexts

SCHEMA_VERSION = 2

SCHEMA = """
create table coverage_schema (
    version integer
);

create table meta (
    has_lines boolean,
    has_arcs boolean,
    sys_argv text
);

create table file (
    id integer primary key,
    path text,
    unique(path)
);

create table context (
    id integer primary key,
    context text,
    unique(context)
);

create table line (
    file_id integer,
    context_id integer,
    lineno integer,
    unique(file_id, context_id, lineno)
);

create table arc (
    file_id integer,
    context_id integer,
    fromno integer,
    tono integer,
    unique(file_id, context_id, fromno, tono)
);

create table tracer (
    file_id integer primary key,
    tracer text
);
"""


class CoverageSqliteData(SimpleReprMixin):
    def __init__(self, basename=None, suffix=None, warn=None, debug=None):
        self._basename = os.path.abspath(basename or ".coverage")
        self._suffix = suffix
        self._warn = warn
        self._debug = debug or NoDebugging()

        self._choose_filename()
        self._file_map = {}
        self._dbs = {}
        self._pid = os.getpid()

        # Are we in sync with the data file?
        self._have_used = False

        self._has_lines = False
        self._has_arcs = False

        self._current_context = None
        self._current_context_id = None

    def _choose_filename(self):
        self._filename = self._basename
        suffix = filename_suffix(self._suffix)
        if suffix:
            self._filename += "." + suffix

    def _reset(self):
        if self._dbs:
            for db in self._dbs.values():
                db.close()
        self._dbs = {}
        self._file_map = {}
        self._have_used = False
        self._current_context_id = None

    def _create_db(self):
        if self._debug.should('dataio'):
            self._debug.write("Creating data file {!r}".format(self._filename))
        self._dbs[get_thread_id()] = Sqlite(self._filename, self._debug)
        with self._dbs[get_thread_id()] as db:
            for stmt in SCHEMA.split(';'):
                stmt = " ".join(stmt.strip().split())
                if stmt:
                    db.execute(stmt)
            db.execute("insert into coverage_schema (version) values (?)", (SCHEMA_VERSION,))
            db.execute(
                "insert into meta (has_lines, has_arcs, sys_argv) values (?, ?, ?)",
                (self._has_lines, self._has_arcs, str(getattr(sys, 'argv', None)))
            )

    def _open_db(self):
        if self._debug.should('dataio'):
            self._debug.write("Opening data file {!r}".format(self._filename))
        self._dbs[get_thread_id()] = Sqlite(self._filename, self._debug)
        with self._dbs[get_thread_id()] as db:
            try:
                schema_version, = db.execute("select version from coverage_schema").fetchone()
            except Exception as exc:
                raise CoverageException(
                    "Data file {!r} doesn't seem to be a coverage data file: {}".format(
                        self._filename, exc
                    )
                )
            else:
                if schema_version != SCHEMA_VERSION:
                    raise CoverageException(
                        "Couldn't use data file {!r}: wrong schema: {} instead of {}".format(
                            self._filename, schema_version, SCHEMA_VERSION
                        )
                    )

            for row in db.execute("select has_lines, has_arcs from meta"):
                self._has_lines, self._has_arcs = row

            for path, id in db.execute("select path, id from file"):
                self._file_map[path] = id

    def _connect(self):
        if get_thread_id() not in self._dbs:
            if os.path.exists(self._filename):
                self._open_db()
            else:
                self._create_db()
        return self._dbs[get_thread_id()]

    def __nonzero__(self):
        if (get_thread_id() not in self._dbs and not os.path.exists(self._filename)):
            return False
        try:
            with self._connect() as con:
                rows = con.execute("select * from file limit 1")
                return bool(list(rows))
        except CoverageException:
            return False

    __bool__ = __nonzero__

    def dump(self):                                         # pragma: debugging
        """Write a dump of the database."""
        if self._debug:
            with self._connect() as con:
                self._debug.write(con.dump())

    def _file_id(self, filename, add=False):
        """Get the file id for `filename`.

        If filename is not in the database yet, add it if `add` is True.
        If `add` is not True, return None.
        """
        if filename not in self._file_map:
            if add:
                with self._connect() as con:
                    cur = con.execute("insert or replace into file (path) values (?)", (filename,))
                    self._file_map[filename] = cur.lastrowid
        return self._file_map.get(filename)

    def _context_id(self, context):
        """Get the id for a context."""
        assert context is not None
        self._start_using()
        with self._connect() as con:
            row = con.execute("select id from context where context = ?", (context,)).fetchone()
            if row is not None:
                return row[0]
            else:
                return None

    def set_context(self, context):
        """Set the current context for future `add_lines` etc."""
        if self._debug.should('dataop'):
            self._debug.write("Setting context: %r" % (context,))
        self._current_context = context
        self._current_context_id = None

    def _set_context_id(self):
        """Use the _current_context to set _current_context_id."""
        context = self._current_context or ""
        context_id = self._context_id(context)
        if context_id is not None:
            self._current_context_id = context_id
        else:
            with self._connect() as con:
                cur = con.execute("insert into context (context) values (?)", (context,))
                self._current_context_id = cur.lastrowid

    def base_filename(self):
        """The base filename for storing data."""
        return self._basename

    def data_filename(self):
        """Where is the data stored?"""
        return self._filename

    def add_lines(self, line_data):
        """Add measured line data.

        `line_data` is a dictionary mapping file names to dictionaries::

            { filename: { lineno: None, ... }, ...}

        """
        if self._debug.should('dataop'):
            self._debug.write("Adding lines: %d files, %d lines total" % (
                len(line_data), sum(len(lines) for lines in line_data.values())
            ))
        self._start_using()
        self._choose_lines_or_arcs(lines=True)
        self._set_context_id()
        with self._connect() as con:
            for filename, linenos in iitems(line_data):
                file_id = self._file_id(filename, add=True)
                data = [(file_id, self._current_context_id, lineno) for lineno in linenos]
                con.executemany(
                    "insert or ignore into line (file_id, context_id, lineno) values (?, ?, ?)",
                    data,
                )

    def add_arcs(self, arc_data):
        """Add measured arc data.

        `arc_data` is a dictionary mapping file names to dictionaries::

            { filename: { (l1,l2): None, ... }, ...}

        """
        if self._debug.should('dataop'):
            self._debug.write("Adding arcs: %d files, %d arcs total" % (
                len(arc_data), sum(len(arcs) for arcs in arc_data.values())
            ))
        self._start_using()
        self._choose_lines_or_arcs(arcs=True)
        self._set_context_id()
        with self._connect() as con:
            for filename, arcs in iitems(arc_data):
                file_id = self._file_id(filename, add=True)
                data = [(file_id, self._current_context_id, fromno, tono) for fromno, tono in arcs]
                con.executemany(
                    "insert or ignore into arc (file_id, context_id, fromno, tono) values (?, ?, ?, ?)",
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
        self._start_using()
        with self._connect() as con:
            for filename, plugin_name in iitems(file_tracers):
                file_id = self._file_id(filename)
                if file_id is None:
                    raise CoverageException(
                        "Can't add file tracer data for unmeasured file '%s'" % (filename,)
                    )

                existing_plugin = self.file_tracer(filename)
                if existing_plugin:
                    if existing_plugin != plugin_name:
                        raise CoverageException(
                            "Conflicting file tracer name for '%s': %r vs %r" % (
                                filename, existing_plugin, plugin_name,
                            )
                        )
                elif plugin_name:
                    con.execute(
                        "insert into tracer (file_id, tracer) values (?, ?)",
                        (file_id, plugin_name)
                    )

    def touch_file(self, filename, plugin_name=""):
        """Ensure that `filename` appears in the data, empty if needed.

        `plugin_name` is the name of the plugin resposible for this file. It is used
        to associate the right filereporter, etc.
        """
        self._start_using()
        if self._debug.should('dataop'):
            self._debug.write("Touching %r" % (filename,))
        if not self._has_arcs and not self._has_lines:
            raise CoverageException("Can't touch files in an empty CoverageSqliteData")

        self._file_id(filename, add=True)
        if plugin_name:
            # Set the tracer for this file
            self.add_file_tracers({filename: plugin_name})

    def update(self, other_data, aliases=None):
        """Update this data with data from several other `CoverageData` instances.

        If `aliases` is provided, it's a `PathAliases` object that is used to
        re-map paths to match the local machine's.
        """
        if self._has_lines and other_data._has_arcs:
            raise CoverageException("Can't combine arc data with line data")
        if self._has_arcs and other_data._has_lines:
            raise CoverageException("Can't combine line data with arc data")

        aliases = aliases or PathAliases()

        # Force the database we're writing to to exist before we start nesting
        # contexts.
        self._start_using()

        # Collector for all arcs, lines and tracers
        other_data.read()
        with other_data._connect() as conn:
            # Get files data.
            cur = conn.execute('select path from file')
            files = {path: aliases.map(path) for (path,) in cur}
            cur.close()

            # Get contexts data.
            cur = conn.execute('select context from context')
            contexts = [context for (context,) in cur]
            cur.close()

            # Get arc data.
            cur = conn.execute(
                'select file.path, context.context, arc.fromno, arc.tono '
                'from arc '
                'inner join file on file.id = arc.file_id '
                'inner join context on context.id = arc.context_id'
            )
            arcs = [(files[path], context, fromno, tono) for (path, context, fromno, tono) in cur]
            cur.close()

            # Get line data.
            cur = conn.execute(
                'select file.path, context.context, line.lineno '
                'from line '
                'inner join file on file.id = line.file_id '
                'inner join context on context.id = line.context_id'
            )
            lines = [(files[path], context, lineno) for (path, context, lineno) in cur]
            cur.close()

            # Get tracer data.
            cur = conn.execute(
                'select file.path, tracer '
                'from tracer '
                'inner join file on file.id = tracer.file_id'
            )
            tracers = {files[path]: tracer for (path, tracer) in cur}
            cur.close()

        with self._connect() as conn:
            conn.isolation_level = 'IMMEDIATE'

            # Get all tracers in the DB. Files not in the tracers are assumed
            # to have an empty string tracer. Since Sqlite does not support
            # full outer joins, we have to make two queries to fill the
            # dictionary.
            this_tracers = {path: '' for path, in conn.execute('select path from file')}
            this_tracers.update({
                aliases.map(path): tracer
                for path, tracer in conn.execute(
                    'select file.path, tracer from tracer '
                    'inner join file on file.id = tracer.file_id'
                )
            })

            # Create all file and context rows in the DB.
            conn.executemany(
                'insert or ignore into file (path) values (?)',
                ((file,) for file in files.values())
            )
            file_ids = {
                path: id
                for id, path in conn.execute('select id, path from file')
            }
            conn.executemany(
                'insert or ignore into context (context) values (?)',
                ((context,) for context in contexts)
            )
            context_ids = {
                context: id
                for id, context in conn.execute('select id, context from context')
            }

            # Prepare tracers and fail, if a conflict is found.
            # tracer_paths is used to ensure consistency over the tracer data
            # and tracer_map tracks the tracers to be inserted.
            tracer_map = {}
            for path in files.values():
                this_tracer = this_tracers.get(path)
                other_tracer = tracers.get(path, '')
                # If there is no tracer, there is always the None tracer.
                if this_tracer is not None and this_tracer != other_tracer:
                    raise CoverageException(
                        "Conflicting file tracer name for '%s': %r vs %r" % (
                            path, this_tracer, other_tracer
                        )
                    )
                tracer_map[path] = other_tracer

            # Prepare arc and line rows to be inserted by converting the file
            # and context strings with integer ids. Then use the efficient
            # `executemany()` to insert all rows at once.
            arc_rows = (
                (file_ids[file], context_ids[context], fromno, tono)
                for file, context, fromno, tono in arcs
            )
            line_rows = (
                (file_ids[file], context_ids[context], lineno)
                for file, context, lineno in lines
            )

            self._choose_lines_or_arcs(arcs=bool(arcs), lines=bool(lines))

            conn.executemany(
                'insert or ignore into arc '
                '(file_id, context_id, fromno, tono) values (?, ?, ?, ?)',
                arc_rows
            )
            conn.executemany(
                'insert or ignore into line '
                '(file_id, context_id, lineno) values (?, ?, ?)',
                line_rows
            )
            conn.executemany(
                'insert or ignore into tracer (file_id, tracer) values (?, ?)',
                ((file_ids[filename], tracer) for filename, tracer in tracer_map.items())
            )

        # Update all internal cache data.
        self._reset()
        self.read()

    def erase(self, parallel=False):
        """Erase the data in this object.

        If `parallel` is true, then also deletes data files created from the
        basename by parallel-mode.

        """
        self._reset()
        if self._debug.should('dataio'):
            self._debug.write("Erasing data file {!r}".format(self._filename))
        file_be_gone(self._filename)
        if parallel:
            data_dir, local = os.path.split(self._filename)
            localdot = local + '.*'
            pattern = os.path.join(os.path.abspath(data_dir), localdot)
            for filename in glob.glob(pattern):
                if self._debug.should('dataio'):
                    self._debug.write("Erasing parallel data file {!r}".format(filename))
                file_be_gone(filename)

    def read(self):
        with self._connect():       # TODO: doesn't look right
            self._have_used = True

    def write(self):
        """Write the collected coverage data to a file."""
        pass

    def _start_using(self):
        if self._pid != os.getpid():
            # Looks like we forked! Have to start a new data file.
            self._reset()
            self._choose_filename()
            self._pid = os.getpid()
        if not self._have_used:
            self.erase()
        self._have_used = True

    def has_arcs(self):
        return bool(self._has_arcs)

    def measured_files(self):
        """A set of all files that had been measured."""
        return set(self._file_map)

    def measured_contexts(self):
        """A set of all contexts that have been measured."""
        self._start_using()
        with self._connect() as con:
            contexts = set(row[0] for row in con.execute("select distinct(context) from context"))
        return contexts

    def file_tracer(self, filename):
        """Get the plugin name of the file tracer for a file.

        Returns the name of the plugin that handles this file.  If the file was
        measured, but didn't use a plugin, then "" is returned.  If the file
        was not measured, then None is returned.

        """
        self._start_using()
        with self._connect() as con:
            file_id = self._file_id(filename)
            if file_id is None:
                return None
            row = con.execute("select tracer from tracer where file_id = ?", (file_id,)).fetchone()
            if row is not None:
                return row[0] or ""
            return ""   # File was measured, but no tracer associated.

    def lines(self, filename, context=None):
        self._start_using()
        if self.has_arcs():
            arcs = self.arcs(filename, context=context)
            if arcs is not None:
                all_lines = itertools.chain.from_iterable(arcs)
                return list(set(l for l in all_lines if l > 0))

        with self._connect() as con:
            file_id = self._file_id(filename)
            if file_id is None:
                return None
            else:
                query = "select distinct lineno from line where file_id = ?"
                data = [file_id]
                if context is not None:
                    query += " and context_id = ?"
                    data += [self._context_id(context)]
                linenos = con.execute(query, data)
                return [lineno for lineno, in linenos]

    def arcs(self, filename, context=None):
        self._start_using()
        with self._connect() as con:
            file_id = self._file_id(filename)
            if file_id is None:
                return None
            else:
                query = "select distinct fromno, tono from arc where file_id = ?"
                data = [file_id]
                if context is not None:
                    query += " and context_id = ?"
                    data += [self._context_id(context)]
                arcs = con.execute(query, data)
                return list(arcs)

    def run_infos(self):
        return []   # TODO


class Sqlite(SimpleReprMixin):
    def __init__(self, filename, debug):
        self.debug = debug if debug.should('sql') else None
        self.filename = filename
        self.nest = 0
        if self.debug:
            self.debug.write("Connecting to {!r}".format(filename))

    def connect(self):
        # SQLite on Windows on py2 won't open a file if the filename argument
        # has non-ascii characters in it.  Opening a relative file name avoids
        # a problem if the current directory has non-ascii.
        filename = os.path.relpath(self.filename)
        self.con = sqlite3.connect(filename)

        # This pragma makes writing faster. It disables rollbacks, but we never need them.
        # PyPy needs the .close() calls here, or sqlite gets twisted up:
        # https://bitbucket.org/pypy/pypy/issues/2872/default-isolation-mode-is-different-on
        self.execute("pragma journal_mode=off").close()
        # This pragma makes writing faster.
        self.execute("pragma synchronous=off").close()

    def close(self):
        self.con.close()

    def __enter__(self):
        if self.nest == 0:
            self.connect()
            self.con.__enter__()
        self.nest += 1
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.nest -= 1
        if self.nest == 0:
            self.con.__exit__(exc_type, exc_value, traceback)
            self.close()

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

    def dump(self):                                         # pragma: debugging
        """Return a multi-line string, the dump of the database."""
        return "\n".join(self.con.iterdump())
