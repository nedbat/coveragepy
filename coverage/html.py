# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""HTML reporting for coverage.py."""

import collections
import datetime
import json
import os
import re
import shutil

import coverage
from coverage import env
from coverage.backward import iitems
from coverage.data import add_data_to_hash
from coverage.files import flat_rootname
from coverage.misc import CoverageException, ensure_dir, file_be_gone, Hasher, isolate_module
from coverage.report import get_analysis_to_report
from coverage.results import Numbers
from coverage.templite import Templite

os = isolate_module(os)


# Static files are looked for in a list of places.
STATIC_PATH = [
    # The place Debian puts system Javascript libraries.
    "/usr/share/javascript",

    # Our htmlfiles directory.
    os.path.join(os.path.dirname(__file__), "htmlfiles"),
]


def data_filename(fname, pkgdir=""):
    """Return the path to a data file of ours.

    The file is searched for on `STATIC_PATH`, and the first place it's found,
    is returned.

    Each directory in `STATIC_PATH` is searched as-is, and also, if `pkgdir`
    is provided, at that sub-directory.

    """
    tried = []
    for static_dir in STATIC_PATH:
        static_filename = os.path.join(static_dir, fname)
        if os.path.exists(static_filename):
            return static_filename
        else:
            tried.append(static_filename)
        if pkgdir:
            static_filename = os.path.join(static_dir, pkgdir, fname)
            if os.path.exists(static_filename):
                return static_filename
            else:
                tried.append(static_filename)
    raise CoverageException(
        "Couldn't find static file %r from %r, tried: %r" % (fname, os.getcwd(), tried)
    )


def read_data(fname):
    """Return the contents of a data file of ours."""
    with open(data_filename(fname)) as data_file:
        return data_file.read()


def write_html(fname, html):
    """Write `html` to `fname`, properly encoded."""
    html = re.sub(r"(\A\s+)|(\s+$)", "", html, flags=re.MULTILINE) + "\n"
    with open(fname, "wb") as fout:
        fout.write(html.encode('ascii', 'xmlcharrefreplace'))


class HtmlReporter(object):
    """HTML reporting."""

    # These files will be copied from the htmlfiles directory to the output
    # directory.
    STATIC_FILES = [
        ("style.css", ""),
        ("jquery.min.js", "jquery"),
        ("jquery.ba-throttle-debounce.min.js", "jquery-throttle-debounce"),
        ("jquery.hotkeys.js", "jquery-hotkeys"),
        ("jquery.isonscreen.js", "jquery-isonscreen"),
        ("jquery.tablesorter.min.js", "jquery-tablesorter"),
        ("coverage_html.js", ""),
        ("keybd_closed.png", ""),
        ("keybd_open.png", ""),
    ]

    def __init__(self, cov, config):
        self.coverage = cov
        self.config = config
        self.directory = None
        title = self.config.html_title
        if env.PY2:
            title = title.decode("utf8")

        if self.config.extra_css:
            self.extra_css = os.path.basename(self.config.extra_css)
        else:
            self.extra_css = None

        self.template_globals = {
            'escape': escape,
            'pair': pair,
            'title': title,
            'len': len,
            '__url__': coverage.__url__,
            '__version__': coverage.__version__,
            'time_stamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
            'extra_css': self.extra_css,
        }
        self.pyfile_html_source = read_data("pyfile.html")
        self.source_tmpl = Templite(self.pyfile_html_source, self.template_globals)

        self.data = self.coverage.get_data()

        self.files = []
        self.all_files_nums = []
        self.has_arcs = self.data.has_arcs()
        self.status = HtmlStatus()
        self.totals = Numbers()

    def report(self, morfs):
        """Generate an HTML report for `morfs`.

        `morfs` is a list of modules or file names.

        """
        # Read the status data.
        self.status.read(self.config.html_dir)

        # Check that this run used the same settings as the last run.
        m = Hasher()
        m.update(self.config)
        m.update(self.pyfile_html_source)
        these_settings = m.hexdigest()
        if self.status.settings_hash() != these_settings:
            self.status.reset()
            self.status.set_settings_hash(these_settings)

        self.directory = self.config.html_dir

        # Process all the files.
        self.coverage.get_data().set_query_contexts(self.config.query_contexts)
        for fr, analysis in get_analysis_to_report(self.coverage, self.config, morfs):
            self.html_file(fr, analysis)

        if not self.all_files_nums:
            raise CoverageException("No data to report.")

        # Write the index file.
        self.index_file()

        self.make_local_static_report_files()
        return self.totals.n_statements and self.totals.pc_covered

    def make_local_static_report_files(self):
        """Make local instances of static files for HTML report."""
        # The files we provide must always be copied.
        for static, pkgdir in self.STATIC_FILES:
            shutil.copyfile(
                data_filename(static, pkgdir),
                os.path.join(self.directory, static)
            )

        # The user may have extra CSS they want copied.
        if self.extra_css:
            shutil.copyfile(
                self.config.extra_css,
                os.path.join(self.directory, self.extra_css)
            )

    def file_hash(self, fr):
        """Compute a hash that changes if the file needs to be re-reported."""
        m = Hasher()
        m.update(fr.source().encode('utf-8'))
        add_data_to_hash(self.data, fr.filename, m)
        return m.hexdigest()

    def html_file(self, fr, analysis):
        """Generate an HTML file for one source file."""
        rootname = flat_rootname(fr.relative_filename())
        html_filename = rootname + ".html"
        ensure_dir(self.directory)
        html_path = os.path.join(self.directory, html_filename)

        # Get the numbers for this file.
        nums = analysis.numbers
        self.all_files_nums.append(nums)

        if self.config.skip_covered:
            # Don't report on 100% files.
            no_missing_lines = (nums.n_missing == 0)
            no_missing_branches = (nums.n_partial_branches == 0)
            if no_missing_lines and no_missing_branches:
                # If there's an existing file, remove it.
                file_be_gone(html_path)
                return

        # Find out if the file on disk is already correct.
        this_hash = self.file_hash(fr)
        that_hash = self.status.file_hash(rootname)
        if this_hash == that_hash:
            # Nothing has changed to require the file to be reported again.
            self.files.append(self.status.index_info(rootname))
            return

        self.status.set_file_hash(rootname, this_hash)

        # Write the HTML page for this file.
        file_data = self.data_for_file(fr, analysis)
        for ldata in file_data['lines']:
            # Build the HTML for the line.
            html = []
            for tok_type, tok_text in ldata['tokens']:
                if tok_type == "ws":
                    html.append(escape(tok_text))
                else:
                    tok_html = escape(tok_text) or '&nbsp;'
                    html.append(
                        '<span class="{}">{}</span>'.format(tok_type, tok_html)
                    )
            ldata['html'] = ''.join(html)

            if ldata['short_annotations']:
                # 202F is NARROW NO-BREAK SPACE.
                # 219B is RIGHTWARDS ARROW WITH STROKE.
                ldata['annotate'] = ",&nbsp;&nbsp; ".join(
                    "{}&#x202F;&#x219B;&#x202F;{}".format(ldata['number'], d)
                    for d in ldata['short_annotations']
                    )
            else:
                ldata['annotate'] = None

            if ldata['long_annotations']:
                longs = ldata['long_annotations']
                if len(longs) == 1:
                    ldata['annotate_long'] = longs[0]
                else:
                    ldata['annotate_long'] = "{:d} missed branches: {}".format(
                        len(longs),
                        ", ".join(
                            "{:d}) {}".format(num, ann_long)
                            for num, ann_long in enumerate(longs, start=1)
                            ),
                    )
            else:
                ldata['annotate_long'] = None

        html = self.source_tmpl.render(file_data)
        write_html(html_path, html)

        # Save this file's information for the index file.
        index_info = {
            'nums': nums,
            'html_filename': html_filename,
            'relative_filename': fr.relative_filename(),
        }
        self.files.append(index_info)
        self.status.set_index_info(rootname, index_info)

    def data_for_file(self, fr, analysis):
        if self.has_arcs:
            missing_branch_arcs = analysis.missing_branch_arcs()
            arcs_executed = analysis.arcs_executed()

        # These classes determine which lines are highlighted by default.
        c_run = "run hide_run"
        c_exc = "exc"
        c_mis = "mis"
        c_par = "par " + c_run

        contexts_by_lineno = collections.defaultdict(list)
        if self.config.show_contexts:
            # Lookup line number contexts.
            contexts_by_lineno = analysis.data.contexts_by_lineno(fr.filename)

        lines = []

        for lineno, tokens in enumerate(fr.source_token_lines(), start=1):
            # Figure out how to mark this line.
            line_class = []
            short_annotations = []
            long_annotations = []

            if lineno in analysis.statements:
                line_class.append("stm")

            if lineno in analysis.excluded:
                line_class.append(c_exc)
            elif lineno in analysis.missing:
                line_class.append(c_mis)
            elif self.has_arcs and lineno in missing_branch_arcs:
                line_class.append(c_par)
                for b in missing_branch_arcs[lineno]:
                    if b < 0:
                        short_annotations.append("exit")
                    else:
                        short_annotations.append(b)
                    long_annotations.append(fr.missing_arc_description(lineno, b, arcs_executed))
            elif lineno in analysis.statements:
                line_class.append(c_run)

            if self.config.show_contexts:
                contexts = sorted(filter(None, contexts_by_lineno[lineno]))
            else:
                contexts = None

            lines.append({
                'tokens': tokens,
                'number': lineno,
                'class': ' '.join(line_class) or "pln",
                'contexts': contexts,
                'short_annotations': short_annotations,
                'long_annotations': long_annotations,
            })

        file_data = {
            'c_exc': c_exc,
            'c_mis': c_mis,
            'c_par': c_par,
            'c_run': c_run,
            'has_arcs': self.has_arcs,
            'show_contexts': self.config.show_contexts,
            'relative_filename': fr.relative_filename(),
            'nums': analysis.numbers,
            'lines': lines,
        }

        return file_data

    def index_file(self):
        """Write the index.html file for this report."""
        index_tmpl = Templite(read_data("index.html"), self.template_globals)

        self.totals = sum(self.all_files_nums)

        html = index_tmpl.render({
            'has_arcs': self.has_arcs,
            'files': self.files,
            'totals': self.totals,
        })

        write_html(os.path.join(self.directory, "index.html"), html)

        # Write the latest hashes for next time.
        self.status.write(self.directory)


class HtmlStatus(object):
    """The status information we keep to support incremental reporting."""

    STATUS_FILE = "status.json"
    STATUS_FORMAT = 1

    #           pylint: disable=wrong-spelling-in-comment,useless-suppression
    #  The data looks like:
    #
    #  {
    #      'format': 1,
    #      'settings': '540ee119c15d52a68a53fe6f0897346d',
    #      'version': '4.0a1',
    #      'files': {
    #          'cogapp___init__': {
    #              'hash': 'e45581a5b48f879f301c0f30bf77a50c',
    #              'index': {
    #                  'html_filename': 'cogapp___init__.html',
    #                  'name': 'cogapp/__init__',
    #                  'nums': <coverage.results.Numbers object at 0x10ab7ed0>,
    #              }
    #          },
    #          ...
    #          'cogapp_whiteutils': {
    #              'hash': '8504bb427fc488c4176809ded0277d51',
    #              'index': {
    #                  'html_filename': 'cogapp_whiteutils.html',
    #                  'name': 'cogapp/whiteutils',
    #                  'nums': <coverage.results.Numbers object at 0x10ab7d90>,
    #              }
    #          },
    #      },
    #  }

    def __init__(self):
        self.reset()

    def reset(self):
        """Initialize to empty."""
        self.settings = ''
        self.files = {}

    def read(self, directory):
        """Read the last status in `directory`."""
        usable = False
        try:
            status_file = os.path.join(directory, self.STATUS_FILE)
            with open(status_file) as fstatus:
                status = json.load(fstatus)
        except (IOError, ValueError):
            usable = False
        else:
            usable = True
            if status['format'] != self.STATUS_FORMAT:
                usable = False
            elif status['version'] != coverage.__version__:
                usable = False

        if usable:
            self.files = {}
            for filename, fileinfo in iitems(status['files']):
                fileinfo['index']['nums'] = Numbers(*fileinfo['index']['nums'])
                self.files[filename] = fileinfo
            self.settings = status['settings']
        else:
            self.reset()

    def write(self, directory):
        """Write the current status to `directory`."""
        status_file = os.path.join(directory, self.STATUS_FILE)
        files = {}
        for filename, fileinfo in iitems(self.files):
            fileinfo['index']['nums'] = fileinfo['index']['nums'].init_args()
            files[filename] = fileinfo

        status = {
            'format': self.STATUS_FORMAT,
            'version': coverage.__version__,
            'settings': self.settings,
            'files': files,
        }
        with open(status_file, "w") as fout:
            json.dump(status, fout, separators=(',', ':'))

        # Older versions of ShiningPanda look for the old name, status.dat.
        # Accommodate them if we are running under Jenkins.
        # https://issues.jenkins-ci.org/browse/JENKINS-28428
        if "JENKINS_URL" in os.environ:
            with open(os.path.join(directory, "status.dat"), "w") as dat:
                dat.write("https://issues.jenkins-ci.org/browse/JENKINS-28428\n")

    def settings_hash(self):
        """Get the hash of the coverage.py settings."""
        return self.settings

    def set_settings_hash(self, settings):
        """Set the hash of the coverage.py settings."""
        self.settings = settings

    def file_hash(self, fname):
        """Get the hash of `fname`'s contents."""
        return self.files.get(fname, {}).get('hash', '')

    def set_file_hash(self, fname, val):
        """Set the hash of `fname`'s contents."""
        self.files.setdefault(fname, {})['hash'] = val

    def index_info(self, fname):
        """Get the information for index.html for `fname`."""
        return self.files.get(fname, {}).get('index', {})

    def set_index_info(self, fname, info):
        """Set the information for index.html for `fname`."""
        self.files.setdefault(fname, {})['index'] = info


# Helpers for templates and generating HTML

def escape(t):
    """HTML-escape the text in `t`.

    This is only suitable for HTML text, not attributes.

    """
    # Convert HTML special chars into HTML entities.
    return t.replace("&", "&amp;").replace("<", "&lt;")


def pair(ratio):
    """Format a pair of numbers so JavaScript can read them in an attribute."""
    return "%s %s" % ratio
