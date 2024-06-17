# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Run performance comparisons for versions of coverage"""

from __future__ import annotations

import collections
import contextlib
import itertools
import json
import os
import random
import shutil
import statistics
import subprocess
import sys
import time

from pathlib import Path

from dataclasses import dataclass
from typing import Any, Iterable, Iterator, Tuple

import requests
import tabulate


class ShellSession:
    """A logged shell session.

    The duration of the last command is available as .last_duration.
    """

    def __init__(self, output_filename: str):
        self.output_filename = output_filename
        self.last_duration: float = 0
        self.foutput = None
        self.env_vars = {"PATH": os.getenv("PATH")}

    def __enter__(self):
        self.foutput = open(self.output_filename, "a", encoding="utf-8")
        print(f"Logging output to {os.path.abspath(self.output_filename)}")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.foutput.close()

    @contextlib.contextmanager
    def set_env(self, env_vars):
        old_env_vars = self.env_vars
        if env_vars:
            self.env_vars = dict(old_env_vars)
            self.env_vars.update(env_vars)
        try:
            yield
        finally:
            self.env_vars = old_env_vars

    def print(self, *args, **kwargs):
        """Print a message to this shell's log."""
        print(*args, **kwargs, file=self.foutput)

    def print_banner(self, *args, **kwargs):
        """Print a distinguished banner to the log."""
        self.print("\n######> ", end="")
        self.print(*args, **kwargs)

    def run_command(self, cmd: str) -> str:
        """
        Run a command line (with a shell).

        Returns:
            str: the output of the command.

        """
        self.print(f"\n### ========================\n$ {cmd}")
        start = time.perf_counter()
        proc = subprocess.run(
            cmd,
            shell=True,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=self.env_vars,
        )
        output = proc.stdout.decode("utf-8")
        self.last_duration = time.perf_counter() - start
        self.print(output, end="")
        self.print(f"(was: {cmd})")
        self.print(f"(in {os.getcwd()}, duration: {self.last_duration:.3f}s)")

        if proc.returncode != 0:
            self.print(f"ERROR: command returned {proc.returncode}")
            raise Exception(
                f"Command failed ({proc.returncode}): {cmd!r}, output was:\n{output}"
            )

        return output.strip()


def rmrf(path: Path) -> None:
    """
    Remove a directory tree.  It's OK if it doesn't exist.
    """
    if path.exists():
        shutil.rmtree(path)


@contextlib.contextmanager
def change_dir(newdir: Path) -> Iterator[Path]:
    """
    Change to a new directory, and then change back.

    Will make the directory if needed.
    """
    old_dir = os.getcwd()
    newdir.mkdir(parents=True, exist_ok=True)
    os.chdir(newdir)
    try:
        yield newdir
    finally:
        os.chdir(old_dir)


@contextlib.contextmanager
def file_replace(file_name: Path, old_text: str, new_text: str) -> Iterator[None]:
    """
    Replace some text in `file_name`, and change it back.
    """
    if old_text:
        file_text = file_name.read_text()
        if old_text not in file_text:
            raise Exception("Old text {old_text!r} not found in {file_name}")
        updated_text = file_text.replace(old_text, new_text)
        file_name.write_text(updated_text)
    try:
        yield
    finally:
        if old_text:
            file_name.write_text(file_text)


def file_must_exist(file_name: str, kind: str = "file") -> Path:
    """
    Check that a file exists, for early validation of pip (etc) arguments.

    Raises an exception if it doesn't exist.  Returns the resolved path if it
    does exist so we can use relative paths and they'll still work once we've
    cd'd to the temporary workspace.
    """
    path = Path(file_name).expanduser().resolve()
    if not path.exists():
        kind = kind[0].upper() + kind[1:]
        raise RuntimeError(f"{kind} {file_name!r} doesn't exist")
    return path


def url_must_exist(url: str) -> bool:
    """
    Check that a URL exists, for early validation of pip (etc) arguments.

    Raises an exception if it doesn't exist.
    """
    resp = requests.head(url)
    resp.raise_for_status()
    return True


class ProjectToTest:
    """Information about a project to use as a test case."""

    # Where can we clone the project from?
    git_url: str | None = None
    slug: str | None = None

    def __init__(self):
        url_must_exist(self.git_url)
        if not self.slug:
            if self.git_url:
                self.slug = self.git_url.split("/")[-1]

    def shell(self):
        return ShellSession(f"output_{self.slug}.log")

    def make_dir(self):
        self.dir = Path(f"work_{self.slug}")
        if self.dir.exists():
            rmrf(self.dir)

    def get_source(self, shell, retries=5):
        """Get the source of the project."""
        for retry in range(retries):
            try:
                shell.run_command(f"git clone {self.git_url} {self.dir}")
                return
            except Exception as e:
                print(f"Retrying to clone {self.git_url} due to error:\n{e}")
                if retry == retries - 1:
                    raise e

    def prep_environment(self, env):
        """Prepare the environment to run the test suite.

        This is not timed.
        """
        pass

    @contextlib.contextmanager
    def tweak_coverage_settings(
        self, settings: Iterable[tuple[str, Any]]
    ) -> Iterator[None]:
        """Tweak the coverage settings.

        NOTE: This is not properly factored, and is only used by ToxProject now!!!
        """
        yield

    def pre_check(self, env):
        pass

    def post_check(self, env):
        pass

    def run_no_coverage(self, env):
        """Run the test suite with no coverage measurement.

        Returns the duration of the run.
        """
        pass

    def run_with_coverage(self, env, pip_args, cov_tweaks):
        """Run the test suite with coverage measurement.

        Must install a particular version of coverage using `pip_args`.

        Returns the duration of the run.
        """
        pass


class EmptyProject(ProjectToTest):
    """A dummy project for testing other parts of this code."""

    def __init__(self, slug: str = "empty", fake_durations: Iterable[float] = (1.23,)):
        self.slug = slug
        self.durations = iter(itertools.cycle(fake_durations))

    def get_source(self, shell):
        pass

    def run_no_coverage(self, env):
        """Run the test suite with coverage measurement."""
        return next(self.durations)

    def run_with_coverage(self, env, pip_args, cov_tweaks):
        """Run the test suite with coverage measurement."""
        return next(self.durations)


class ToxProject(ProjectToTest):
    """A project using tox to run the test suite."""

    def prep_environment(self, env):
        env.shell.run_command(f"{env.python} -m pip install tox")
        self.run_tox(env, env.pyver.toxenv, "--notest")

    def run_tox(self, env, toxenv, toxargs=""):
        """Run a tox command. Return the duration."""
        env.shell.run_command(f"{env.python} -m tox -v -e {toxenv} {toxargs}")
        return env.shell.last_duration

    def run_no_coverage(self, env):
        return self.run_tox(env, env.pyver.toxenv, "--skip-pkg-install")

    def run_with_coverage(self, env, pip_args, cov_tweaks):
        self.run_tox(env, env.pyver.toxenv, "--notest")
        env.shell.run_command(
            f".tox/{env.pyver.toxenv}/bin/python -m pip install {pip_args}"
        )
        with self.tweak_coverage_settings(cov_tweaks):
            self.pre_check(env)  # NOTE: Not properly factored, and only used from here.
            duration = self.run_tox(env, env.pyver.toxenv, "--skip-pkg-install")
            self.post_check(
                env
            )  # NOTE: Not properly factored, and only used from here.
        return duration


class ProjectPytestHtml(ToxProject):
    """pytest-dev/pytest-html"""

    git_url = "https://github.com/pytest-dev/pytest-html"

    def run_with_coverage(self, env, pip_args, cov_tweaks):
        raise Exception("This doesn't work because options changed to tweaks")
        covenv = env.pyver.toxenv + "-cov"
        self.run_tox(env, covenv, "--notest")
        env.shell.run_command(f".tox/{covenv}/bin/python -m pip install {pip_args}")
        if cov_tweaks:
            replace = ("# reference: https", f"[run]\n{cov_tweaks}\n#")
        else:
            replace = ("", "")
        with file_replace(Path(".coveragerc"), *replace):
            env.shell.run_command("cat .coveragerc")
            env.shell.run_command(f".tox/{covenv}/bin/python -m coverage debug sys")
            return self.run_tox(env, covenv, "--skip-pkg-install")


class ProjectDateutil(ToxProject):
    """dateutil/dateutil"""

    git_url = "https://github.com/dateutil/dateutil"

    def prep_environment(self, env):
        super().prep_environment(env)
        env.shell.run_command(f"{env.python} updatezinfo.py")

    def run_no_coverage(self, env):
        env.shell.run_command("echo No option to run without coverage")
        return 0


class ProjectAttrs(ToxProject):
    """python-attrs/attrs"""

    git_url = "https://github.com/python-attrs/attrs"

    def tweak_coverage_settings(
        self, tweaks: Iterable[tuple[str, Any]]
    ) -> Iterator[None]:
        return tweak_toml_coverage_settings("pyproject.toml", tweaks)

    def pre_check(self, env):
        env.shell.run_command("cat pyproject.toml")

    def post_check(self, env):
        env.shell.run_command("ls -al")


class ProjectDjangoAuthToolkit(ToxProject):
    """jazzband/django-oauth-toolkit"""

    git_url = "https://github.com/jazzband/django-oauth-toolkit"

    def run_no_coverage(self, env):
        env.shell.run_command("echo No option to run without coverage")
        return 0


class ProjectDjango(ToxProject):
    """django/django"""
    # brew install libmemcached
    # pip install -e .
    # coverage run tests/runtests.py --settings=test_sqlite
    # coverage report --format=total --precision=6
    # 32.848540


class ProjectMashumaro(ProjectToTest):
    git_url = "https://github.com/Fatal1ty/mashumaro"

    def __init__(self, more_pytest_args=""):
        super().__init__()
        self.more_pytest_args = more_pytest_args

    def prep_environment(self, env):
        env.shell.run_command(f"{env.python} -m pip install .")
        env.shell.run_command(f"{env.python} -m pip install -r requirements-dev.txt")

    def run_no_coverage(self, env):
        env.shell.run_command(f"{env.python} -m pytest {self.more_pytest_args}")
        return env.shell.last_duration

    def run_with_coverage(self, env, pip_args, cov_tweaks):
        env.shell.run_command(f"{env.python} -m pip install {pip_args}")
        env.shell.run_command(
            f"{env.python} -m pytest --cov=mashumaro --cov=tests {self.more_pytest_args}"
        )
        duration = env.shell.last_duration
        report = env.shell.run_command(f"{env.python} -m coverage report --precision=6")
        print("Results:", report.splitlines()[-1])
        return duration


class ProjectMashumaroBranch(ProjectMashumaro):
    def __init__(self, more_pytest_args=""):
        super().__init__(more_pytest_args="--cov-branch " + more_pytest_args)
        self.slug = "mashbranch"


class ProjectOperator(ProjectToTest):
    git_url = "https://github.com/nedbat/operator"

    def __init__(self, more_pytest_args=""):
        super().__init__()
        self.more_pytest_args = more_pytest_args

    def prep_environment(self, env):
        env.shell.run_command(f"{env.python} -m pip install tox")
        Path("/tmp/operator_tmp").mkdir(exist_ok=True)
        env.shell.run_command(f"{env.python} -m tox -e unit --notest")
        env.shell.run_command(f"{env.python} -m tox -e unitnocov --notest")

    def run_no_coverage(self, env):
        env.shell.run_command(
            f"TMPDIR=/tmp/operator_tmp {env.python} -m tox -e unitnocov --skip-pkg-install -- {self.more_pytest_args}"
        )
        return env.shell.last_duration

    def run_with_coverage(self, env, pip_args, cov_tweaks):
        env.shell.run_command(f"{env.python} -m pip install {pip_args}")
        env.shell.run_command(
            f"TMPDIR=/tmp/operator_tmp {env.python} -m tox -e unit --skip-pkg-install -- {self.more_pytest_args}"
        )
        duration = env.shell.last_duration
        report = env.shell.run_command(f"{env.python} -m coverage report --precision=6")
        print("Results:", report.splitlines()[-1])
        return duration


class ProjectPygments(ToxProject):
    git_url = "https://github.com/pygments/pygments"

    def run_with_coverage(self, env, pip_args, cov_tweaks):
        self.run_tox(env, env.pyver.toxenv, "--notest")
        env.shell.run_command(
            f".tox/{env.pyver.toxenv}/bin/python -m pip install {pip_args}"
        )
        with self.tweak_coverage_settings(cov_tweaks):
            self.pre_check(env)  # NOTE: Not properly factored, and only used from here.
            duration = self.run_tox(env, env.pyver.toxenv, "--skip-pkg-install -- --cov")
            self.post_check(
                env
            )  # NOTE: Not properly factored, and only used from here.
        return duration


class ProjectRich(ToxProject):
    git_url = "https://github.com/Textualize/rich"

    def prep_environment(self, env):
        raise Exception("Doesn't work due to poetry install error.")


class ProjectTornado(ToxProject):
    git_url = "https://github.com/tornadoweb/tornado"

    def run_no_coverage(self, env):
        env.shell.run_command(f"{env.python} -m tornado.test")
        return env.shell.last_duration

    def run_with_coverage(self, env, pip_args, cov_tweaks):
        env.shell.run_command(f"{env.python} -m pip install {pip_args}")
        env.shell.run_command(
            f"{env.python} -m coverage run -m tornado.test"
        )
        duration = env.shell.last_duration
        report = env.shell.run_command(f"{env.python} -m coverage report --precision=6")
        print("Results:", report.splitlines()[-1])
        return duration


class ProjectDulwich(ToxProject):
    git_url = "https://github.com/jelmer/dulwich"

    def prep_environment(self, env):
        env.shell.run_command(f"{env.python} -m pip install -r requirements.txt")
        env.shell.run_command(f"{env.python} -m pip install .")

    def run_no_coverage(self, env):
        env.shell.run_command(f"{env.python} -m unittest tests.test_suite")
        return env.shell.last_duration

    def run_with_coverage(self, env, pip_args, cov_tweaks):
        env.shell.run_command(f"{env.python} -m pip install {pip_args}")
        env.shell.run_command(
            f"{env.python} -m coverage run -m unittest tests.test_suite"
        )
        duration = env.shell.last_duration
        report = env.shell.run_command(f"{env.python} -m coverage report --precision=6")
        print("Results:", report.splitlines()[-1])
        return duration


class ProjectBlack(ToxProject):
    git_url = "https://github.com/psf/black"

    def prep_environment(self, env):
        env.shell.run_command(f"{env.python} -m pip install -r test_requirements.txt")
        env.shell.run_command(f"{env.python} -m pip install -e .[d]")

    def run_no_coverage(self, env):
        env.shell.run_command(
            f"{env.python} -m pytest tests --run-optional no_jupyter --no-cov --numprocesses 1"
        )
        return env.shell.last_duration

    def run_with_coverage(self, env, pip_args, cov_tweaks):
        env.shell.run_command(f"{env.python} -m pip install {pip_args}")
        env.shell.run_command(
            f"{env.python} -m pytest tests --run-optional no_jupyter --cov --numprocesses 1"
        )
        duration = env.shell.last_duration
        report = env.shell.run_command(f"{env.python} -m coverage report --precision=6")
        print("Results:", report.splitlines()[-1])
        return duration


class ProjectMpmath(ProjectToTest):
    git_url = "https://github.com/mpmath/mpmath"
    select = "-k 'not (torture or extra or functions2 or calculus or cli or elliptic or quad)'"

    def prep_environment(self, env):
        env.shell.run_command(f"{env.python} -m pip install .[develop]")

    def run_no_coverage(self, env):
        env.shell.run_command(f"{env.python} -m pytest {self.select} --no-cov")
        return env.shell.last_duration

    def run_with_coverage(self, env, pip_args, cov_tweaks):
        env.shell.run_command(
            f"{env.python} -m pytest {self.select} --cov=mpmath"
        )
        duration = env.shell.last_duration
        report = env.shell.run_command(f"{env.python} -m coverage report --precision=6")
        print("Results:", report.splitlines()[-1])
        return duration


class ProjectMypy(ToxProject):
    git_url = "https://github.com/python/mypy"

    # Slow test suites
    CMDLINE = "PythonCmdline"
    PEP561 = "PEP561Suite"
    EVALUATION = "PythonEvaluation"
    DAEMON = "testdaemon"
    STUBGEN_CMD = "StubgenCmdLine"
    STUBGEN_PY = "StubgenPythonSuite"
    MYPYC_RUN = "TestRun"
    MYPYC_RUN_MULTI = "TestRunMultiFile"
    MYPYC_EXTERNAL = "TestExternal"
    MYPYC_COMMAND_LINE = "TestCommandLine"
    ERROR_STREAM = "ErrorStreamSuite"

    ALL_NON_FAST = [
        CMDLINE,
        PEP561,
        EVALUATION,
        DAEMON,
        STUBGEN_CMD,
        STUBGEN_PY,
        MYPYC_RUN,
        MYPYC_RUN_MULTI,
        MYPYC_EXTERNAL,
        MYPYC_COMMAND_LINE,
        ERROR_STREAM,
    ]

    FAST = "pytest", "-k", f"\"not ({' or '.join(ALL_NON_FAST)})\""

    def prep_environment(self, env):
        env.shell.run_command(f"{env.python} -m pip install -r test-requirements.txt")

    def run_no_coverage(self, env):
        env.shell.run_command(f"{env.python} -m {' '.join(self.FAST)} --no-cov")
        return env.shell.last_duration

    def run_with_coverage(self, env, pip_args, cov_tweaks):
        env.shell.run_command(f"{env.python} -m pip install {pip_args}")
        env.shell.run_command(
            f"{env.python} -m {' '.join(self.FAST)} --cov"
        )
        duration = env.shell.last_duration
        report = env.shell.run_command(f"{env.python} -m coverage report --precision=6")
        print("Results:", report.splitlines()[-1])
        return duration


class ProjectHtml5lib(ToxProject):
    git_url = "https://github.com/html5lib/html5lib-python"

    def prep_environment(self, env):
        env.shell.run_command(f"{env.python} -m pip install -r requirements-test.txt")
        env.shell.run_command(f"{env.python} -m pip install .")

    def run_no_coverage(self, env):
        env.shell.run_command(f"{env.python} -m pytest")
        return env.shell.last_duration

    def run_with_coverage(self, env, pip_args, cov_tweaks):
        env.shell.run_command(f"{env.python} -m pip install {pip_args}")
        env.shell.run_command(
            f"{env.python} -m coverage run -m pytest"
        )
        duration = env.shell.last_duration
        report = env.shell.run_command(f"{env.python} -m coverage report --precision=6")
        print("Results:", report.splitlines()[-1])
        return duration


class ProjectSphinx(ToxProject):
    git_url = "https://github.com/sphinx-doc/sphinx"

    def prep_environment(self, env):
        env.shell.run_command(f"{env.python} -m pip install .[test]")

    def run_no_coverage(self, env):
        env.shell.run_command(f"{env.python} -m pytest")
        return env.shell.last_duration

    def run_with_coverage(self, env, pip_args, cov_tweaks):
        env.shell.run_command(f"{env.python} -m pip install {pip_args}")
        env.shell.run_command(
            f"{env.python} -m coverage run -m pytest"
        )
        duration = env.shell.last_duration
        env.shell.run_command(f"{env.python} -m coverage combine")
        report = env.shell.run_command(f"{env.python} -m coverage report --precision=6")
        print("Results:", report.splitlines()[-1])
        return duration


class ProjectUrllib3(ProjectToTest):
    git_url = "https://github.com/urllib3/urllib3"

    def prep_environment(self, env):
        env.shell.run_command(f"{env.python} -m pip install -r dev-requirements.txt")
        env.shell.run_command(f"{env.python} -m pip install .")

    def run_no_coverage(self, env):
        env.shell.run_command(f"{env.python} -m pytest")
        return env.shell.last_duration

    def run_with_coverage(self, env, pip_args, cov_tweaks):
        env.shell.run_command(f"{env.python} -m pip install {pip_args}")
        env.shell.run_command(
            f"{env.python} -m coverage run -m pytest"
        )
        duration = env.shell.last_duration
        report = env.shell.run_command(f"{env.python} -m coverage report --precision=6")
        print("Results:", report.splitlines()[-1])
        return duration


def tweak_toml_coverage_settings(
    toml_file: str, tweaks: Iterable[tuple[str, Any]]
) -> Iterator[None]:
    if tweaks:
        toml_inserts = []
        for name, value in tweaks:
            if isinstance(value, bool):
                toml_inserts.append(f"{name} = {str(value).lower()}")
            elif isinstance(value, str):
                toml_inserts.append(f"{name} = '{value}'")
            else:
                raise Exception(f"Can't tweak toml setting: {name} = {value!r}")
        header = "[tool.coverage.run]\n"
        insert = header + "\n".join(toml_inserts) + "\n"
    else:
        header = insert = ""
    return file_replace(Path(toml_file), header, insert)


class AdHocProject(ProjectToTest):
    """A standalone program to run locally."""

    def __init__(self, python_file, cur_dir=None, pip_args=None):
        super().__init__()
        self.python_file = Path(python_file)
        if not self.python_file.exists():
            raise ValueError(f"Couldn't find {self.python_file} to run ad-hoc.")
        self.cur_dir = Path(cur_dir or self.python_file.parent)
        if not self.cur_dir.exists():
            raise ValueError(f"Couldn't find {self.cur_dir} to run in.")
        self.pip_args = pip_args
        self.slug = self.python_file.name

    def get_source(self, shell):
        pass

    def prep_environment(self, env):
        env.shell.run_command(f"{env.python} -m pip install {self.pip_args}")

    def run_no_coverage(self, env):
        with change_dir(self.cur_dir):
            env.shell.run_command(f"{env.python} {self.python_file}")
        return env.shell.last_duration

    def run_with_coverage(self, env, pip_args, cov_tweaks):
        env.shell.run_command(f"{env.python} -m pip install {pip_args}")
        with change_dir(self.cur_dir):
            env.shell.run_command(f"{env.python} -m coverage run {self.python_file}")
        return env.shell.last_duration


class SlipcoverBenchmark(AdHocProject):
    """
    For running code from the Slipcover benchmarks.

    Clone https://github.com/plasma-umass/slipcover to /src/slipcover

    """

    def __init__(self, python_file):
        super().__init__(
            python_file=f"/src/slipcover/benchmarks/{python_file}",
            cur_dir="/src/slipcover",
            pip_args="six pyperf",
        )


class PyVersion:
    """A version of Python to use."""

    # The command to run this Python
    command: str
    # Short word for messages, directories, etc
    slug: str
    # The tox environment to run this Python
    toxenv: str


class Python(PyVersion):
    """A version of CPython to use."""

    def __init__(self, major, minor):
        self.command = self.slug = f"python{major}.{minor}"
        self.toxenv = f"py{major}{minor}"


class PyPy(PyVersion):
    """A version of PyPy to use."""

    def __init__(self, major, minor):
        self.command = self.slug = f"pypy{major}.{minor}"
        self.toxenv = f"pypy{major}{minor}"


class AdHocPython(PyVersion):
    """A custom build of Python to use."""

    def __init__(self, path, slug):
        self.command = f"{path}/bin/python3"
        file_must_exist(self.command, "python command")
        self.slug = slug
        self.toxenv = None


@dataclass
class Coverage:
    """A version of coverage.py to use, maybe None."""

    # Short word for messages, directories, etc
    slug: str
    # Arguments for "pip install ..."
    pip_args: str | None = None
    # Tweaks to the .coveragerc file
    tweaks: Iterable[tuple[str, Any]] | None = None
    # Environment variables to set
    env_vars: dict[str, str] | None = None


class NoCoverage(Coverage):
    """Run without coverage at all."""

    def __init__(self, slug="nocov"):
        super().__init__(slug=slug, pip_args=None)


class CoveragePR(Coverage):
    """A version of coverage.py from a pull request."""

    def __init__(self, number, tweaks=None, env_vars=None):
        url = f"https://github.com/nedbat/coveragepy.git@refs/pull/{number}/merge"
        url_must_exist(url)
        super().__init__(
            slug=f"#{number}",
            pip_args=f"git+{url}",
            tweaks=tweaks,
            env_vars=env_vars,
        )


class CoverageCommit(Coverage):
    """A version of coverage.py from a specific commit."""

    def __init__(self, sha, tweaks=None, env_vars=None):
        url = f"https://github.com/nedbat/coveragepy.git@{sha}",
        url_must_exist(url)
        super().__init__(
            slug=sha,
            pip_args=f"git+{url}",
            tweaks=tweaks,
            env_vars=env_vars,
        )


class CoverageSource(Coverage):
    """The coverage.py in a working tree."""

    def __init__(self, directory, slug="source", tweaks=None, env_vars=None):
        directory = file_must_exist(directory, "coverage directory")
        super().__init__(
            slug=slug,
            pip_args=str(directory),
            tweaks=tweaks,
            env_vars=env_vars,
        )


@dataclass
class Env:
    """An environment to run a test suite in."""

    pyver: PyVersion
    python: Path
    shell: ShellSession


ResultKey = Tuple[str, str, str]

DIMENSION_NAMES = ["proj", "pyver", "cov"]


class Experiment:
    """A particular time experiment to run."""

    def __init__(
        self,
        py_versions: list[PyVersion],
        cov_versions: list[Coverage],
        projects: list[ProjectToTest],
        results_file: str = "results.json",
        load: bool = False,
        cwd: str = "",
    ):
        self.py_versions = py_versions
        self.cov_versions = cov_versions
        self.projects = projects
        self.results_file = Path(cwd) / Path(results_file)
        self.result_data: dict[ResultKey, list[float]] = self.load_results() if load else {}
        self.summary_data: dict[ResultKey, float] = {}

    def save_results(self):
        """Save current results to the JSON file."""
        with self.results_file.open("w") as f:
            json.dump({ " ".join(k): v for k, v in self.result_data.items()}, f)

    def load_results(self) -> dict[ResultKey, list[float]]:
        """Load results from the JSON file if it exists."""
        if self.results_file.exists():
            with self.results_file.open("r") as f:
                data: dict[str, list[float]] = json.load(f)
            return {tuple(k.split()): v for k, v in data.items()}
        return {}

    def run(self, num_runs: int = 3) -> None:
        total_runs = (
            len(self.projects)
            * len(self.py_versions)
            * len(self.cov_versions)
            * num_runs
        )
        total_run_nums = iter(itertools.count(start=1))

        all_runs = []

        for proj in self.projects:
            with proj.shell() as shell:
                print(f"Prepping project {proj.slug}")
                shell.print_banner(f"Prepping project {proj.slug}")
                proj.make_dir()
                proj.get_source(shell)

                for pyver in self.py_versions:
                    print(f"Making venv for {proj.slug} {pyver.slug}")
                    venv_dir = f"venv_{proj.slug}_{pyver.slug}"
                    shell.run_command(f"{pyver.command} -m venv {venv_dir}")
                    python = Path.cwd() / f"{venv_dir}/bin/python"
                    shell.run_command(f"{python} -V")
                    shell.run_command(f"{python} -m pip install -U pip")
                    env = Env(pyver, python, shell)

                    with change_dir(proj.dir):
                        print(f"Prepping for {proj.slug} {pyver.slug}")
                        proj.prep_environment(env)
                        for cov_ver in self.cov_versions:
                            all_runs.append((proj, pyver, cov_ver, env))

        all_runs *= num_runs
        random.shuffle(all_runs)

        run_data: dict[ResultKey, list[float]] = collections.defaultdict(list)
        run_data.update(self.result_data)

        for proj, pyver, cov_ver, env in all_runs:
            result_key = (proj.slug, pyver.slug, cov_ver.slug)
            total_run_num = next(total_run_nums)
            if result_key in self.result_data and len(self.result_data[result_key]) >= num_runs:
                print(f"Skipping {result_key} as results already exist.")
                continue

            with env.shell:
                banner = (
                    "Running tests: "
                    + f"proj={proj.slug}, py={pyver.slug}, cov={cov_ver.slug}, "
                    + f"{total_run_num} of {total_runs}"
                )
                print(banner)
                env.shell.print_banner(banner)
                with change_dir(proj.dir):
                    with env.shell.set_env(cov_ver.env_vars):
                        if cov_ver.pip_args is None:
                            dur = proj.run_no_coverage(env)
                        else:
                            dur = proj.run_with_coverage(
                                env,
                                cov_ver.pip_args,
                                cov_ver.tweaks,
                            )
            print(f"Tests took {dur:.3f}s")
            if result_key not in self.result_data:
                self.result_data[result_key] = []
            self.result_data[result_key].append(dur)
            run_data[result_key].append(dur)
            self.save_results()
        # Summarize and collect the data.
        print("# Results")
        for proj in self.projects:
            for pyver in self.py_versions:
                for cov_ver in self.cov_versions:
                    result_key = (proj.slug, pyver.slug, cov_ver.slug)
                    data = run_data[result_key]
                    med = statistics.median(data)
                    self.summary_data[result_key] = med
                    stdev = statistics.stdev(data) if len(data) > 1 else 0.0
                    summary = (
                        f"Median for {proj.slug}, {pyver.slug}, {cov_ver.slug}: "
                        + f"{med:.3f}s, "
                        + f"stdev={stdev:.3f}"
                    )
                    if 1:
                        data_sum = ", ".join(f"{d:.3f}" for d in data)
                        summary += f", data={data_sum}"
                    print(summary)

    def show_results(
        self,
        rows: list[str],
        column: str,
        ratios: Iterable[tuple[str, str, str]] = (),
    ) -> None:
        dimensions = {
            "cov": [cov_ver.slug for cov_ver in self.cov_versions],
            "pyver": [pyver.slug for pyver in self.py_versions],
            "proj": [proj.slug for proj in self.projects],
        }

        table_axes = [dimensions[rowname] for rowname in rows]
        data_order = [*rows, column]
        remap = [data_order.index(datum) for datum in DIMENSION_NAMES]

        header = []
        header.extend(rows)
        header.extend(dimensions[column])
        header.extend(slug for slug, _, _ in ratios)

        aligns = ["left"] * len(rows) + ["right"] * (len(header) - len(rows))
        data = []

        for tup in itertools.product(*table_axes):
            row = []
            row.extend(tup)
            col_data = {}
            for col in dimensions[column]:
                key = (*tup, col)
                key = tuple(key[i] for i in remap)
                result_time = self.summary_data[key]
                row.append(f"{result_time:.1f}s")
                col_data[col] = result_time
            for _, num, denom in ratios:
                ratio = col_data[num] / col_data[denom]
                row.append(f"{ratio * 100:.0f}%")
            data.append(row)

        print()
        print(tabulate.tabulate(data, headers=header, colalign=aligns, tablefmt="pipe"))


PERF_DIR = Path("/tmp/covperf")


def run_experiment(
    py_versions: list[PyVersion],
    cov_versions: list[Coverage],
    projects: list[ProjectToTest],
    rows: list[str],
    column: str,
    ratios: Iterable[tuple[str, str, str]] = (),
    num_runs: int = int(sys.argv[1]),
    load: bool = False,
):
    """
    Run a benchmarking experiment and print a table of results.

    Arguments:

        py_versions: The Python versions to test.
        cov_versions: The coverage versions to test.
        projects: The projects to run.
        rows: A list of strings chosen from `"pyver"`, `"cov"`, and `"proj"`.
        column: The remaining dimension not used in `rows`.
        ratios: A list of triples: (title, slug1, slug2).
        num_runs: The number of times to run each matrix element.

    """
    slugs = [v.slug for v in py_versions + cov_versions + projects]
    if len(set(slugs)) != len(slugs):
        raise Exception(f"Slugs must be unique: {slugs}")
    if any(" " in slug for slug in slugs):
        raise Exception(f"No spaces in slugs please: {slugs}")
    ratio_slugs = [rslug for ratio in ratios for rslug in ratio[1:]]
    if any(rslug not in slugs for rslug in ratio_slugs):
        raise Exception(f"Ratio slug doesn't match a slug: {ratio_slugs}, {slugs}")
    if set(rows + [column]) != set(DIMENSION_NAMES):
        raise Exception(
            f"All of these must be in rows or column: {', '.join(DIMENSION_NAMES)}"
        )

    print(f"Removing and re-making {PERF_DIR}")
    rmrf(PERF_DIR)

    cwd = str(Path.cwd())
    with change_dir(PERF_DIR):
        exp = Experiment(
            py_versions=py_versions, cov_versions=cov_versions, projects=projects, load=load, cwd=cwd
        )
        exp.run(num_runs=int(num_runs))
        exp.show_results(rows=rows, column=column, ratios=ratios)
