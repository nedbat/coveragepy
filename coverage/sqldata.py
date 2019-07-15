# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Sqlite coverage data."""

# TODO: get sys_info for data class, so we can see sqlite version etc
# TODO: factor out dataop debugging to a wrapper class?
# TODO: make sure all dataop debugging is in place somehow
# TODO: should writes be batched?
# TODO: run_info

import collections
import glob
import itertools
import os
import sqlite3
import sys

from coverage.backward import get_thread_id, iitems
from coverage.backward import bytes_to_ints, binary_bytes, zip_longest
from coverage.debug import NoDebugging, SimpleReprMixin
from coverage import env
from coverage.files import PathAliases
from coverage.misc import CoverageException, file_be_gone, filename_suffix, isolate_module
from coverage.misc import contract

os = isolate_module(os)

SCHEMA_VERSION = 3

SCHEMA = """
CREATE TABLE coverage_schema (
    -- One row, to record the version of the schema store in this db.
    version integer
    -- Schema versions:
    -- 1: Released in 5.0a2
    -- 2: Added contexts in 5.0a3.
    -- 3: Replaced line table with line_map table.
);

CREATE TABLE meta (
    -- One row, to record some metadata about the data
    has_lines boolean,      -- Is this data recording lines?
    has_arcs boolean,       -- .. or branches?
    sys_argv text           -- The coverage command line that recorded the data.
);

CREATE TABLE file (
    -- A row per file measured.
    id integer primary key,
    path text,
    unique(path)
);

CREATE TABLE context (
    -- A row per context measured.
    id integer primary key,
    context text,
    unique(context)
);

CREATE TABLE line_map (
    -- If recording lines, a row per context per line executed.
    file_id integer,            -- foreign key to `file`.
    context_id integer,         -- foreign key to `context`.
    bitmap blob,                -- Nth bit represents line N.
    unique(file_id, context_id)
);

CREATE TABLE arc (
    -- If recording branches, a row per context per from/to line transition executed.
    file_id integer,            -- foreign key to `file`.
    context_id integer,         -- foreign key to `context`.
    fromno integer,             -- line number jumped from.
    tono integer,               -- line number jumped to.
    unique(file_id, context_id, fromno, tono)
);

CREATE TABLE tracer (
    -- A row per file indicating the tracer used for that file.
    file_id integer primary key,
    tracer text
);
"""

if env.PY2:
    def to_blob(bytes):
        return buffer(bytes)
    def from_blob(blob):
        return bytes(blob)
else:
    def to_blob(bytes):
        return bytes
    def from_blob(blob):
        return blob


class CoverageData(SimpleReprMixin):
    """Manages collected coverage data, including file storage.

    TODO: This is the 4.x docstring. Update it for 5.0.

    This class is the public supported API to the data coverage.py collects
    during program execution.  It includes information about what code was
    executed. It does not include information from the analysis phase, to
    determine what lines could have been executed, or what lines were not
    executed.

    .. note::

        The file format is not documented or guaranteed.  It will change in
        the future, in possibly complicated ways.  Do not read coverage.py
        data files directly.  Use this API to avoid disruption.

    There are a number of kinds of data that can be collected:

    * **lines**: the line numbers of source lines that were executed.
      These are always available.

    * **arcs**: pairs of source and destination line numbers for transitions
      between source lines.  These are only available if branch coverage was
      used.

    * **file tracer names**: the module names of the file tracer plugins that
      handled each file in the data.

    * **run information**: information about the program execution.  This is
      written during "coverage run", and then accumulated during "coverage
      combine".

    Lines, arcs, and file tracer names are stored for each source file. File
    names in this API are case-sensitive, even on platforms with
    case-insensitive file systems.

    A data file is associated with the data when the :class:`CoverageData`
    is created.

    To read a coverage.py data file, use :meth:`read`.  You can then
    access the line, arc, or file tracer data with :meth:`lines`, :meth:`arcs`,
    or :meth:`file_tracer`.  Run information is available with
    :meth:`run_infos`.

    The :meth:`has_arcs` method indicates whether arc data is available.  You
    can get a list of the files in the data with :meth:`measured_files`.
    A summary of the line data is available from :meth:`line_counts`.  As with
    most Python containers, you can determine if there is any data at all by
    using this object as a boolean value.

    Most data files will be created by coverage.py itself, but you can use
    methods here to create data files if you like.  The :meth:`add_lines`,
    :meth:`add_arcs`, and :meth:`add_file_tracers` methods add data, in ways
    that are convenient for coverage.py.  The :meth:`add_run_info` method adds
    key-value pairs to the run information.

    To add a source file without any measured data, use :meth:`touch_file`.

    Write the data to its file with :meth:`write`.

    You can clear the data in memory with :meth:`erase`.  Two data collections
    can be combined by using :meth:`update` on one :class:`CoverageData`,
    passing it the other.

    """

    def __init__(self, basename=None, suffix=None, no_disk=False, warn=None, debug=None):
        self._no_disk = no_disk
        self._basename = os.path.abspath(basename or ".coverage")
        self._suffix = suffix
        self._warn = warn
        self._debug = debug or NoDebugging()

        self._choose_filename()
        self._file_map = {}
        # Maps thread ids to SqliteDb objects.
        self._dbs = {}
        self._pid = os.getpid()

        # Are we in sync with the data file?
        self._have_used = False

        self._has_lines = False
        self._has_arcs = False

        self._current_context = None
        self._current_context_id = None
        self._query_contexts = None
        self._query_context_ids = None

    def _choose_filename(self):
        if self._no_disk:
            self._filename = ":memory:"
        else:
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
        self._dbs[get_thread_id()] = db = SqliteDb(self._filename, self._debug)
        with db:
            db.executescript(SCHEMA)
            db.execute("insert into coverage_schema (version) values (?)", (SCHEMA_VERSION,))
            db.execute(
                "insert into meta (has_lines, has_arcs, sys_argv) values (?, ?, ?)",
                (self._has_lines, self._has_arcs, str(getattr(sys, 'argv', None)))
            )

    def _open_db(self):
        if self._debug.should('dataio'):
            self._debug.write("Opening data file {!r}".format(self._filename))
        self._dbs[get_thread_id()] = db = SqliteDb(self._filename, self._debug)
        with db:
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
        """Get the SqliteDb object to use."""
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

    def dumps(self):
        with self._connect() as con:
            return con.dump()

    def loads(self, data):
        if self._debug.should('dataio'):
            self._debug.write("Loading data into data file {!r}".format(self._filename))
        self._dbs[get_thread_id()] = db = SqliteDb(self._filename, self._debug)
        with db:
            db.executescript(data)

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
        if not line_data:
            return
        with self._connect() as con:
            self._set_context_id()
            for filename, linenos in iitems(line_data):
                linemap = nums_to_bitmap(linenos)
                file_id = self._file_id(filename, add=True)
                query = "select bitmap from line_map where file_id = ? and context_id = ?"
                existing = list(con.execute(query, (file_id, self._current_context_id)))
                if existing:
                    linemap = merge_bitmaps(linemap, from_blob(existing[0][0]))

                con.execute(
                    "insert or replace into line_map (file_id, context_id, bitmap) values (?, ?, ?)",
                    (file_id, self._current_context_id, to_blob(linemap)),
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
        if not arc_data:
            return
        with self._connect() as con:
            self._set_context_id()
            for filename, arcs in iitems(arc_data):
                file_id = self._file_id(filename, add=True)
                data = [(file_id, self._current_context_id, fromno, tono) for fromno, tono in arcs]
                con.executemany(
                    "insert or ignore into arc "
                    "(file_id, context_id, fromno, tono) values (?, ?, ?, ?)",
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
        if self._debug.should('dataop'):
            self._debug.write("Adding file tracers: %d files" % (len(file_tracers),))
        if not file_tracers:
            return
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

        `plugin_name` is the name of the plugin responsible for this file. It is used
        to associate the right filereporter, etc.
        """
        self._start_using()
        if self._debug.should('dataop'):
            self._debug.write("Touching %r" % (filename,))
        if not self._has_arcs and not self._has_lines:
            raise CoverageException("Can't touch files in an empty CoverageData")

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
                'select file.path, context.context, line_map.bitmap '
                'from line_map '
                'inner join file on file.id = line_map.file_id '
                'inner join context on context.id = line_map.context_id'
                )
            lines = {(files[path], context): from_blob(bitmap) for (path, context, bitmap) in cur}
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

            # Get line data.
            cur = conn.execute(
                'select file.path, context.context, line_map.bitmap '
                'from line_map '
                'inner join file on file.id = line_map.file_id '
                'inner join context on context.id = line_map.context_id'
                )
            for path, context, bitmap in cur:
                key = (aliases.map(path), context)
                bitmap = from_blob(bitmap)
                if key in lines:
                    bitmap = merge_bitmaps(lines[key], bitmap)
                lines[key] = bitmap
            cur.close()

            self._choose_lines_or_arcs(arcs=bool(arcs), lines=bool(lines))

            # Write the combined data.
            conn.executemany(
                'insert or ignore into arc '
                '(file_id, context_id, fromno, tono) values (?, ?, ?, ?)',
                arc_rows
            )
            conn.execute("delete from line_map")
            conn.executemany(
                "insert into line_map "
                "(file_id, context_id, bitmap) values (?, ?, ?)",
                [(file_ids[file], context_ids[context], to_blob(bitmap)) for (file, context), bitmap in lines.items()]
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


    def set_query_contexts(self, contexts):
        """Set query contexts for future `lines`, `arcs` etc. calls."""
        if contexts:
            self._query_context_ids = self._get_query_context_ids(contexts)
        else:
            self._query_context_ids = None
        self._query_contexts = contexts

    def _get_query_context_ids(self, contexts=None):
        if contexts is not None:
            if not contexts:
                return None
            self._start_using()
            with self._connect() as con:
                context_clause = ' or '.join(['context glob ?'] * len(contexts))
                cur = con.execute("select id from context where " + context_clause, contexts)
                return [row[0] for row in cur.fetchall()]
        elif self._query_contexts:
            return self._query_context_ids
        return None

    def lines(self, filename, contexts=None):
        self._start_using()
        if self.has_arcs():
            arcs = self.arcs(filename, contexts=contexts)
            if arcs is not None:
                all_lines = itertools.chain.from_iterable(arcs)
                return list(set(l for l in all_lines if l > 0))

        with self._connect() as con:
            file_id = self._file_id(filename)
            if file_id is None:
                return None
            else:
                query = "select bitmap from line_map where file_id = ?"
                data = [file_id]
                context_ids = self._get_query_context_ids(contexts)
                if context_ids is not None:
                    ids_array = ', '.join('?'*len(context_ids))
                    query += " and context_id in (" + ids_array + ")"
                    data += context_ids
                bitmaps = list(con.execute(query, data))
                nums = set()
                for row in bitmaps:
                    nums.update(bitmap_to_nums(from_blob(row[0])))
                return sorted(nums)

    def arcs(self, filename, contexts=None):
        self._start_using()
        with self._connect() as con:
            file_id = self._file_id(filename)
            if file_id is None:
                return None
            else:
                query = "select distinct fromno, tono from arc where file_id = ?"
                data = [file_id]
                context_ids = self._get_query_context_ids(contexts)
                if context_ids is not None:
                    ids_array = ', '.join('?'*len(context_ids))
                    query += " and context_id in (" + ids_array + ")"
                    data += context_ids
                arcs = con.execute(query, data)
                return list(arcs)

    def contexts_by_lineno(self, filename):
        lineno_contexts_map = collections.defaultdict(list)
        self._start_using()
        with self._connect() as con:
            file_id = self._file_id(filename)
            if file_id is None:
                return lineno_contexts_map
            if self.has_arcs():
                query = (
                    "select arc.fromno, arc.tono, context.context "
                    "from arc, context "
                    "where arc.file_id = ? and arc.context_id = context.id"
                )
                data = [file_id]
                context_ids = self._get_query_context_ids()
                if context_ids is not None:
                    ids_array = ', '.join('?'*len(context_ids))
                    query += " and arc.context_id in (" + ids_array + ")"
                    data += context_ids
                for fromno, tono, context in con.execute(query, data):
                    if context not in lineno_contexts_map[fromno]:
                        lineno_contexts_map[fromno].append(context)
                    if context not in lineno_contexts_map[tono]:
                        lineno_contexts_map[tono].append(context)
            else:
                query = (
                    "select l.bitmap, c.context from line_map l, context c "
                    "where l.context_id = c.id "
                    "and file_id = ?"
                    )
                data = [file_id]
                context_ids = self._get_query_context_ids()
                if context_ids is not None:
                    ids_array = ', '.join('?'*len(context_ids))
                    query += " and l.context_id in (" + ids_array + ")"
                    data += context_ids
                for bitmap, context in con.execute(query, data):
                    for lineno in bitmap_to_nums(from_blob(bitmap)):
                        lineno_contexts_map[lineno].append(context)
        return lineno_contexts_map

    def run_infos(self):
        return []   # TODO


class SqliteDb(SimpleReprMixin):
    """A simple abstraction over a SQLite database.

    Use as a context manager to get an object you can call
    execute or executemany on.

    """
    def __init__(self, filename, debug):
        self.debug = debug if debug.should('sql') else None
        self.filename = filename
        self.nest = 0
        self.con = None

    def connect(self):
        if self.con is not None:
            return
        # SQLite on Windows on py2 won't open a file if the filename argument
        # has non-ascii characters in it.  Opening a relative file name avoids
        # a problem if the current directory has non-ascii.
        filename = os.path.relpath(self.filename)
        # It can happen that Python switches threads while the tracer writes
        # data. The second thread will also try to write to the data,
        # effectively causing a nested context. However, given the idempotent
        # nature of the tracer operations, sharing a connection among threads
        # is not a problem.
        if self.debug:
            self.debug.write("Connecting to {!r}".format(self.filename))
        self.con = sqlite3.connect(filename, check_same_thread=False)

        # This pragma makes writing faster. It disables rollbacks, but we never need them.
        # PyPy needs the .close() calls here, or sqlite gets twisted up:
        # https://bitbucket.org/pypy/pypy/issues/2872/default-isolation-mode-is-different-on
        self.execute("pragma journal_mode=off").close()
        # This pragma makes writing faster.
        self.execute("pragma synchronous=off").close()

    def close(self):
        if self.con is not None and self.filename != ":memory:":
            self.con.close()
            self.con = None

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

    def executescript(self, script):
        if self.debug:
            self.debug.write("Executing script with {} chars".format(len(script)))
        self.con.executescript(script)

    def dump(self):                                         # pragma: debugging
        """Return a multi-line string, the dump of the database."""
        return "\n".join(self.con.iterdump())


@contract(nums='Iterable', returns='bytes')
def nums_to_bitmap(nums):
    """Convert `nums` (an iterable of ints) into a bitmap."""
    nbytes = max(nums) // 8 + 1
    b = bytearray(nbytes)
    for num in nums:
        b[num//8] |= 1 << num % 8
    return bytes(b)

@contract(bitmap='bytes', returns='list[int]')
def bitmap_to_nums(bitmap):
    """Convert a bitmap into a list of numbers."""
    nums = []
    for byte_i, byte in enumerate(bytes_to_ints(bitmap)):
        for bit_i in range(8):
            if (byte & (1 << bit_i)):
                nums.append(byte_i * 8 + bit_i)
    return nums

@contract(map1='bytes', map2='bytes', returns='bytes')
def merge_bitmaps(map1, map2):
    """Merge two bitmaps"""
    byte_pairs = zip_longest(bytes_to_ints(map1), bytes_to_ints(map2), fillvalue=0)
    return binary_bytes(b1 | b2 for b1, b2 in byte_pairs)
