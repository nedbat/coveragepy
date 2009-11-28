"""Config file for coverage.py"""

import ConfigParser, os


class CoverageConfig(object):
    def __init__(self):
        # Defaults.
        self.cover_pylib = False
        self.timid = False
        self.branch = False
        self.exclude_list = ['# *pragma[: ]*[nN][oO] *[cC][oO][vV][eE][rR]']

    def from_environment(self, env_var):
        # Timidity: for nose users, read an environment variable.  This is a
        # cheap hack, since the rest of the command line arguments aren't
        # recognized, but it solves some users' problems.
        env = os.environ.get(env_var, '')
        if env:
            self.timid = ('--timid' in env)

    def from_args(self, **kwargs):
        for k, v in kwargs.items():
            if v is not None:
                setattr(self, k, v)

    def from_file(self, *files):
        cp = ConfigParser.RawConfigParser()
        cp.read(files)
        
        if cp.has_option('run', 'timid'):
            self.timid = cp.getboolean('run', 'timid')
        if cp.has_option('run', 'cover_pylib'):
            self.cover_pylib = cp.getboolean('run', 'cover_pylib')
        if cp.has_option('run', 'branch'):
            self.branch = cp.getboolean('run', 'branch')
        if cp.has_option('report', 'exclude'):
            self.exclude_list = filter(None, cp.get('report', 'exclude').split('\n'))


if __name__ == '__main__':
    cc = CoverageConfig()
    cc.from_file(".coveragerc", ".coverage.ini")
    import pdb;pdb.set_trace()
    print cc
