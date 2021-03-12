# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""
Test class mixins

Some of these are transitional while working toward pure-pytest style.
"""

import os
import os.path
import sys
import textwrap

import pytest

from coverage import env


class PytestBase(object):
    """A base class to connect to pytest in a test class hierarchy."""

    @pytest.fixture(autouse=True)
    def connect_to_pytest(self, request, monkeypatch):
        """Captures pytest facilities for use by other test helpers."""
        # pylint: disable=attribute-defined-outside-init
        self._pytest_request = request
        self._monkeypatch = monkeypatch
        self.setup_test()

    # Can't call this setUp or setup because pytest sniffs out unittest and
    # nosetest special names, and does things with them.
    # https://github.com/pytest-dev/pytest/issues/8424
    def setup_test(self):
        """Per-test initialization. Override this as you wish."""
        pass

    def addCleanup(self, fn, *args):
        """Like unittest's addCleanup: code to call when the test is done."""
        self._pytest_request.addfinalizer(lambda: fn(*args))

    def set_environ(self, name, value):
        """Set an environment variable `name` to be `value`."""
        self._monkeypatch.setenv(name, value)

    def del_environ(self, name):
        """Delete an environment variable, unless we set it."""
        self._monkeypatch.delenv(name)


class TempDirMixin(object):
    """Provides temp dir and data file helpers for tests."""

    # Our own setting: most of these tests run in their own temp directory.
    # Set this to False in your subclass if you don't want a temp directory
    # created.
    run_in_temp_dir = True

    @pytest.fixture(autouse=True)
    def _temp_dir(self, tmpdir_factory):
        """Create a temp dir for the tests, if they want it."""
        old_dir = None
        if self.run_in_temp_dir:
            tmpdir = tmpdir_factory.mktemp("")
            self.temp_dir = str(tmpdir)
            old_dir = os.getcwd()
            tmpdir.chdir()

            # Modules should be importable from this temp directory.  We don't
            # use '' because we make lots of different temp directories and
            # nose's caching importer can get confused.  The full path prevents
            # problems.
            sys.path.insert(0, os.getcwd())

        try:
            yield None
        finally:
            if old_dir is not None:
                os.chdir(old_dir)

    @pytest.fixture(autouse=True)
    def _save_sys_path(self):
        """Restore sys.path at the end of each test."""
        old_syspath = sys.path[:]
        try:
            yield
        finally:
            sys.path = old_syspath

    @pytest.fixture(autouse=True)
    def _module_saving(self):
        """Remove modules we imported during the test."""
        old_modules = list(sys.modules)
        try:
            yield
        finally:
            added_modules = [m for m in sys.modules if m not in old_modules]
            for m in added_modules:
                del sys.modules[m]

    def make_file(self, filename, text="", bytes=b"", newline=None):
        """Create a file for testing.

        `filename` is the relative path to the file, including directories if
        desired, which will be created if need be.

        `text` is the content to create in the file, a native string (bytes in
        Python 2, unicode in Python 3), or `bytes` are the bytes to write.

        If `newline` is provided, it is a string that will be used as the line
        endings in the created file, otherwise the line endings are as provided
        in `text`.

        Returns `filename`.

        """
        # pylint: disable=redefined-builtin     # bytes
        if bytes:
            data = bytes
        else:
            text = textwrap.dedent(text)
            if newline:
                text = text.replace("\n", newline)
            if env.PY3:
                data = text.encode('utf8')
            else:
                data = text

        # Make sure the directories are available.
        dirs, _ = os.path.split(filename)
        if dirs and not os.path.exists(dirs):
            os.makedirs(dirs)

        # Create the file.
        with open(filename, 'wb') as f:
            f.write(data)

        return filename


class StdStreamCapturingMixin:
    """
    Adapter from the pytest capsys fixture to more convenient methods.

    This doesn't also output to the real stdout, so we probably want to move
    to "real" capsys when we can use fixtures in test methods.

    Once you've used one of these methods, the capturing is reset, so another
    invocation will only return the delta.

    """
    @pytest.fixture(autouse=True)
    def _capcapsys(self, capsys):
        """Grab the fixture so our methods can use it."""
        self.capsys = capsys

    def stdouterr(self):
        """Returns (out, err), two strings for stdout and stderr."""
        return self.capsys.readouterr()

    def stdout(self):
        """Returns a string, the captured stdout."""
        return self.capsys.readouterr().out

    def stderr(self):
        """Returns a string, the captured stderr."""
        return self.capsys.readouterr().err
