# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Tests of miscellaneous stuff."""

from __future__ import annotations

import sys

from typing import Any, Callable, List, cast

import pytest
import setuptools

import coverage
import setup
from coverage import env

from tests.coveragetest import CoverageTest


class SetupPyTest(CoverageTest):
    """Tests of setup.py"""

    run_in_temp_dir = False

    def setUp(self) -> None:
        super().setUp()
        # Force the most restrictive interpretation.
        self.set_environ('LC_ALL', 'C')

    def raise_error(self, error: type[Exception]) -> Callable[[Any], Any]:
        """Return a function that raises the provided exception."""
        def f(*args: Any, **kwargs: Any) -> None:
            raise error
        return f

    def test_metadata(self) -> None:
        status, output = self.run_command_status(
            "python setup.py --description --version --url --author",
        )
        assert status == 0
        out = output.splitlines()
        assert "measurement" in out[0]
        assert coverage.__version__ == out[1]
        assert "github.com/nedbat/coveragepy" in out[2]
        assert "Ned Batchelder" in out[3]

    @pytest.mark.skipif(
        env.PYVERSION[3:5] == ("alpha", 0),
        reason="don't expect classifiers until labelled builds",
    )
    def test_more_metadata(self) -> None:
        # Let's be sure we pick up our own setup.py
        # CoverageTest restores the original sys.path for us.
        sys.path.insert(0, '')
        from setup import setup_args

        classifiers = cast(List[str], setup_args['classifiers'])
        assert len(classifiers) > 7
        assert classifiers[-1].startswith("Development Status ::")
        assert "Programming Language :: Python :: %d" % sys.version_info[:1] in classifiers
        assert "Programming Language :: Python :: %d.%d" % sys.version_info[:2] in classifiers

        long_description = cast(str, setup_args['long_description']).splitlines()
        assert len(long_description) > 7
        assert long_description[0].strip() != ""
        assert long_description[-1].strip() != ""

    def test_build_extension(self) -> None:
        # Do we handle all expected errors?
        for ext_error in setup.ext_errors:
            with pytest.raises(setup.BuildFailed):
                setup.build_ext.build_extension = self.raise_error(ext_error)
                ext_builder = setup.ve_build_ext(setuptools.Distribution())
                ext_builder.build_extension(1)  # type: ignore

        # Sanity check: we don't handle unexpected errors
        for other_error in (ImportError, ZeroDivisionError, Exception):
            with pytest.raises(other_error):
                setup.build_ext.build_extension = self.raise_error(other_error)
                ext_builder = setup.ve_build_ext(setuptools.Distribution())
                ext_builder.build_extension(1)  # type: ignore

    def test_run(self) -> None:
        # `ve_build_ext.run()` only catches `PlatformError` and raises `BuildFailed`
        with pytest.raises(setup.BuildFailed):
            setup.build_ext.run = self.raise_error(setup.errors.PlatformError)
            ext_builder = setup.ve_build_ext(setuptools.Distribution())
            ext_builder.run()  # type: ignore

        # Sanity check: we don't handle unexpected errors
        for error in setup.ext_errors:
            with pytest.raises(error):
                setup.build_ext.build_extension = self.raise_error(error)
                ext_builder = setup.ve_build_ext(setuptools.Distribution())
                ext_builder.build_extension(1)  # type: ignore

    def test_main(self) -> None:
        # `main()` will catch `BuildFailed` once, then it'll be raised again
        # when `setup` is called a second time.
        with pytest.raises(setup.BuildFailed):
            setup.setup = self.raise_error(setup.BuildFailed)
            setup.setup_args["ext_modules"] = "dummy"
            setup.main()  # type: ignore

        # Sanity check: we don't handle unexpected errors
        for error in setup.ext_errors:
            with pytest.raises(error):
                setup.setup_args["ext_modules"] = "dummy"
                setup.setup = self.raise_error(error)
                setup.main()  # type: ignore
