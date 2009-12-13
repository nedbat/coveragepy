"""Config file for coverage.py"""

import os
from coverage.backward import configparser          # pylint: disable-msg=W0622


class CoverageConfig(object):
    """Coverage.py configuration.

    The attributes of this class are the various settings that control the
    operation of coverage.py.

    """

    def __init__(self):
        """Initialize the configuration attributes to their defaults."""
        # Defaults.
        self.cover_pylib = False
        self.timid = False
        self.branch = False
        self.exclude_list = ['# *pragma[: ]*[nN][oO] *[cC][oO][vV][eE][rR]']
        self.data_file = ".coverage"

    def from_environment(self, env_var):
        """Read configuration from the `env_var` environment variable."""
        # Timidity: for nose users, read an environment variable.  This is a
        # cheap hack, since the rest of the command line arguments aren't
        # recognized, but it solves some users' problems.
        env = os.environ.get(env_var, '')
        if env:
            self.timid = ('--timid' in env)

    def from_args(self, **kwargs):
        """Read config values from `kwargs`."""
        for k, v in kwargs.items():
            if v is not None:
                setattr(self, k, v)

    def from_file(self, *files):
        """Read configurating from .rc files.

        Each argument in `files` is a file name to read.

        """
        cp = configparser.RawConfigParser()
        cp.read(files)

        if cp.has_option('run', 'timid'):
            self.timid = cp.getboolean('run', 'timid')
        if cp.has_option('run', 'cover_pylib'):
            self.cover_pylib = cp.getboolean('run', 'cover_pylib')
        if cp.has_option('run', 'branch'):
            self.branch = cp.getboolean('run', 'branch')
        if cp.has_option('report', 'exclude_lines'):
            # Exclude is a list of lines, leave out the blank ones.
            exclude_list = cp.get('report', 'exclude_lines')
            self.exclude_list = list(filter(None, exclude_list.split('\n')))
        if cp.has_option('run', 'data_file'):
            self.data_file = cp.get('run', 'data_file')
