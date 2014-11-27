"""Config file for coverage.py"""

import os, re, sys
from coverage.backward import string_class, iitems
from coverage.misc import CoverageException


# In py3, ConfigParser was renamed to the more-standard configparser
try:
    import configparser
except ImportError:
    import ConfigParser as configparser


class HandyConfigParser(configparser.RawConfigParser):
    """Our specialization of ConfigParser."""

    def __init__(self, section_prefix):
        # pylint: disable=super-init-not-called
        configparser.RawConfigParser.__init__(self)
        self.section_prefix = section_prefix

    def read(self, filename):
        """Read a filename as UTF-8 configuration data."""
        kwargs = {}
        if sys.version_info >= (3, 2):
            kwargs['encoding'] = "utf-8"
        return configparser.RawConfigParser.read(self, filename, **kwargs)

    def has_option(self, section, option):
        section = self.section_prefix + section
        return configparser.RawConfigParser.has_option(self, section, option)

    def has_section(self, section):
        section = self.section_prefix + section
        return configparser.RawConfigParser.has_section(self, section)

    def options(self, section):
        section = self.section_prefix + section
        return configparser.RawConfigParser.options(self, section)

    def get_section(self, section):
        """Get the contents of a section, as a dictionary."""
        d = {}
        for opt in self.options(section):
            d[opt] = self.get(section, opt)
        return d

    def get(self, section, *args, **kwargs):
        """Get a value, replacing environment variables also.

        The arguments are the same as `RawConfigParser.get`, but in the found
        value, ``$WORD`` or ``${WORD}`` are replaced by the value of the
        environment variable ``WORD``.

        Returns the finished value.

        """
        section = self.section_prefix + section
        v = configparser.RawConfigParser.get(self, section, *args, **kwargs)
        def dollar_replace(m):
            """Called for each $replacement."""
            # Only one of the groups will have matched, just get its text.
            word = next(w for w in m.groups() if w is not None)
            if word == "$":
                return "$"
            else:
                return os.environ.get(word, '')

        dollar_pattern = r"""(?x)   # Use extended regex syntax
            \$(?:                   # A dollar sign, then
            (?P<v1>\w+) |           #   a plain word,
            {(?P<v2>\w+)} |         #   or a {-wrapped word,
            (?P<char>[$])           #   or a dollar sign.
            )
            """
        v = re.sub(dollar_pattern, dollar_replace, v)
        return v

    def getlist(self, section, option):
        """Read a list of strings.

        The value of `section` and `option` is treated as a comma- and newline-
        separated list of strings.  Each value is stripped of whitespace.

        Returns the list of strings.

        """
        value_list = self.get(section, option)
        values = []
        for value_line in value_list.split('\n'):
            for value in value_line.split(','):
                value = value.strip()
                if value:
                    values.append(value)
        return values

    def getlinelist(self, section, option):
        """Read a list of full-line strings.

        The value of `section` and `option` is treated as a newline-separated
        list of strings.  Each value is stripped of whitespace.

        Returns the list of strings.

        """
        value_list = self.get(section, option)
        return list(filter(None, value_list.split('\n')))


# The default line exclusion regexes.
DEFAULT_EXCLUDE = [
    r'(?i)#\s*pragma[:\s]?\s*no\s*cover',
    ]

# The default partial branch regexes, to be modified by the user.
DEFAULT_PARTIAL = [
    r'(?i)#\s*pragma[:\s]?\s*no\s*branch',
    ]

# The default partial branch regexes, based on Python semantics.
# These are any Python branching constructs that can't actually execute all
# their branches.
DEFAULT_PARTIAL_ALWAYS = [
    'while (True|1|False|0):',
    'if (True|1|False|0):',
    ]


class CoverageConfig(object):
    """Coverage.py configuration.

    The attributes of this class are the various settings that control the
    operation of coverage.py.

    """
    def __init__(self):
        """Initialize the configuration attributes to their defaults."""
        # Metadata about the config.
        self.attempted_config_files = []
        self.config_files = []

        # Defaults for [run]
        self.branch = False
        self.concurrency = None
        self.cover_pylib = False
        self.data_file = ".coverage"
        self.parallel = False
        self.timid = False
        self.source = None
        self.debug = []
        self.plugins = []

        # Defaults for [report]
        self.exclude_list = DEFAULT_EXCLUDE[:]
        self.fail_under = 0
        self.ignore_errors = False
        self.include = None
        self.omit = None
        self.partial_list = DEFAULT_PARTIAL[:]
        self.partial_always_list = DEFAULT_PARTIAL_ALWAYS[:]
        self.precision = 0
        self.show_missing = False
        self.skip_covered = False

        # Defaults for [html]
        self.html_dir = "htmlcov"
        self.extra_css = None
        self.html_title = "Coverage report"

        # Defaults for [xml]
        self.xml_output = "coverage.xml"

        # Defaults for [paths]
        self.paths = {}

        # Options for plugins
        self.plugin_options = {}

    MUST_BE_LIST = ["omit", "include", "debug", "plugins"]

    def from_args(self, **kwargs):
        """Read config values from `kwargs`."""
        for k, v in iitems(kwargs):
            if v is not None:
                if k in self.MUST_BE_LIST and isinstance(v, string_class):
                    v = [v]
                setattr(self, k, v)

    def from_file(self, filename, section_prefix=""):
        """Read configuration from a .rc file.

        `filename` is a file name to read.

        Returns True or False, whether the file could be read.

        """
        self.attempted_config_files.append(filename)

        cp = HandyConfigParser(section_prefix)
        try:
            files_read = cp.read(filename)
        except configparser.Error as err:
            raise CoverageException(
                "Couldn't read config file %s: %s" % (filename, err)
                )
        if not files_read:
            return False

        self.config_files.extend(files_read)

        try:
            for option_spec in self.CONFIG_FILE_OPTIONS:
                self._set_attr_from_config_option(cp, *option_spec)
        except ValueError as err:
            raise CoverageException(
                "Couldn't read config file %s: %s" % (filename, err)
                )

        # [paths] is special
        if cp.has_section('paths'):
            for option in cp.options('paths'):
                self.paths[option] = cp.getlist('paths', option)

        # plugins can have options
        for plugin in self.plugins:
            if cp.has_section(plugin):
                self.plugin_options[plugin] = cp.get_section(plugin)

        return True

    CONFIG_FILE_OPTIONS = [
        # These are *args for _set_attr_from_config_option:
        #   (attr, where, type_="")
        #
        #   attr is the attribute to set on the CoverageConfig object.
        #   where is the section:name to read from the configuration file.
        #   type_ is the optional type to apply, by using .getTYPE to read the
        #       configuration value from the file.

        # [run]
        ('branch', 'run:branch', 'boolean'),
        ('concurrency', 'run:concurrency'),
        ('cover_pylib', 'run:cover_pylib', 'boolean'),
        ('data_file', 'run:data_file'),
        ('debug', 'run:debug', 'list'),
        ('plugins', 'run:plugins', 'list'),
        ('include', 'run:include', 'list'),
        ('omit', 'run:omit', 'list'),
        ('parallel', 'run:parallel', 'boolean'),
        ('source', 'run:source', 'list'),
        ('timid', 'run:timid', 'boolean'),

        # [report]
        ('exclude_list', 'report:exclude_lines', 'linelist'),
        ('fail_under', 'report:fail_under', 'int'),
        ('ignore_errors', 'report:ignore_errors', 'boolean'),
        ('include', 'report:include', 'list'),
        ('omit', 'report:omit', 'list'),
        ('partial_list', 'report:partial_branches', 'linelist'),
        ('partial_always_list', 'report:partial_branches_always', 'linelist'),
        ('precision', 'report:precision', 'int'),
        ('show_missing', 'report:show_missing', 'boolean'),
        ('skip_covered', 'report:skip_covered', 'boolean'),

        # [html]
        ('html_dir', 'html:directory'),
        ('extra_css', 'html:extra_css'),
        ('html_title', 'html:title'),

        # [xml]
        ('xml_output', 'xml:output'),
        ]

    def _set_attr_from_config_option(self, cp, attr, where, type_=''):
        """Set an attribute on self if it exists in the ConfigParser."""
        section, option = where.split(":")
        if cp.has_option(section, option):
            method = getattr(cp, 'get'+type_)
            setattr(self, attr, method(section, option))

    def get_plugin_options(self, plugin):
        """Get a dictionary of options for the plugin named `plugin`."""
        return self.plugin_options.get(plugin, {})

    # TODO: docs for this.
    def __setitem__(self, option_name, value):
        # Check all the hard-coded options.
        for option_spec in self.CONFIG_FILE_OPTIONS:
            attr, where = option_spec[:2]
            if where == option_name:
                setattr(self, attr, value)
                return

        # See if it's a plugin option.
        plugin_name, _, key = option_name.partition(":")
        if key and plugin_name in self.plugins:
            self.plugin_options.setdefault(plugin_name, {})[key] = value
            return

        # If we get here, we didn't find the option.
        raise CoverageException("No such option: %r" % option_name)

    # TODO: docs for this.
    def __getitem__(self, option_name):
        # Check all the hard-coded options.
        for option_spec in self.CONFIG_FILE_OPTIONS:
            attr, where = option_spec[:2]
            if where == option_name:
                return getattr(self, attr)

        # See if it's a plugin option.
        plugin_name, _, key = option_name.partition(":")
        if key and plugin_name in self.plugins:
            return self.plugin_options.get(plugin_name, {}).get(key)

        # If we get here, we didn't find the option.
        raise CoverageException("No such option: %r" % option_name)
