"""Run performance comparisons for versions of coverage"""

import contextlib
import dataclasses
import os
import shutil
import statistics
import subprocess
import time
from pathlib import Path

from typing import Iterator, List, Optional, Tuple, Union


class ShellSession:
    """A logged shell session.

    The duration of the last command is available as .last_duration.
    """

    def __init__(self, output_filename: str):
        self.output_filename = output_filename
        self.last_duration: float = 0

    def __enter__(self):
        self.foutput = open(self.output_filename, "a", encoding="utf-8")
        print(f"Logging output to {os.path.abspath(self.output_filename)}")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.foutput.close()

    def print(self, *args, **kwargs):
        print(*args, **kwargs, file=self.foutput)

    def run_command(self, cmd: str) -> str:
        """
        Run a command line (with a shell).

        Returns:
            str: the output of the command.

        """
        self.print(f"\n========================\n$ {cmd}")
        start = time.perf_counter()
        proc = subprocess.run(
            cmd,
            shell=True,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
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


class ProjectToTest:
    """Information about a project to use as a test case."""

    # Where can we clone the project from?
    git_url: Optional[str] = None

    def __init__(self):
        self.slug = self.git_url.split("/")[-1]
        self.dir = Path(self.slug)

    def get_source(self, shell):
        """Get the source of the project."""
        if self.dir.exists():
            rmrf(self.dir)
        shell.run_command(f"git clone {self.git_url}")

    def prep_environment(self, env):
        """Prepare the environment to run the test suite.

        This is not timed.
        """
        pass

    def run_no_coverage(self, env):
        """Run the test suite with no coverage measurement."""
        pass

    def run_with_coverage(self, env, pip_args, cov_options):
        """Run the test suite with coverage measurement."""
        pass


class ToxProject(ProjectToTest):
    """A project using tox to run the test suite."""

    def prep_environment(self, env):
        env.shell.run_command(f"{env.python} -m pip install tox")
        self.run_tox(env, env.pyver.toxenv, "--notest")

    def run_tox(self, env, toxenv, toxargs=""):
        env.shell.run_command(f"{env.python} -m tox -e {toxenv} {toxargs}")
        return env.shell.last_duration

    def run_no_coverage(self, env):
        return self.run_tox(env, env.pyver.toxenv, "--skip-pkg-install")


class PytestHtml(ToxProject):
    """pytest-dev/pytest-html"""

    git_url = "https://github.com/pytest-dev/pytest-html"

    def run_with_coverage(self, env, pip_args, cov_options):
        covenv = env.pyver.toxenv + "-cov"
        self.run_tox(env, covenv, "--notest")
        env.shell.run_command(f".tox/{covenv}/bin/python -m pip install {pip_args}")
        if cov_options:
            replace = ("# reference: https", f"[run]\n{cov_options}\n#")
        else:
            replace = ("", "")
        with file_replace(Path(".coveragerc"), *replace):
            env.shell.run_command("cat .coveragerc")
            env.shell.run_command(f".tox/{covenv}/bin/python -m coverage debug sys")
            return self.run_tox(env, covenv, "--skip-pkg-install")


class PyVersion:
    # The command to run this Python
    command: str
    # The tox environment to run this Python
    toxenv: str


class Python(PyVersion):
    """A version of CPython to use."""

    def __init__(self, major, minor):
        self.command = f"python{major}.{minor}"
        self.toxenv = f"py{major}{minor}"


class PyPy(PyVersion):
    """A version of PyPy to use."""

    def __init__(self, major, minor):
        self.command = f"pypy{major}.{minor}"
        self.toxenv = f"pypy{major}{minor}"


@dataclasses.dataclass
class Env:
    """An environment to run a test suite in."""

    pyver: PyVersion
    python: Path
    shell: ShellSession


def run_experiments(
    py_versions: List[PyVersion],
    cov_versions: List[Tuple[str, Optional[str], Optional[str]]],
    projects: List[ProjectToTest],
    num_runs=3,
):
    """Run test suites under different conditions."""

    for proj in projects:
        print(f"Testing with {proj.git_url}")
        with ShellSession(f"output_{proj.slug}.log") as shell:
            proj.get_source(shell)

            for pyver in py_versions:
                print(f"Making venv for {proj.slug} {pyver.command}")
                venv_dir = f"venv_{proj.slug}_{pyver.command}"
                shell.run_command(f"{pyver.command} -m venv {venv_dir}")
                python = Path.cwd() / f"{venv_dir}/bin/python"
                shell.run_command(f"{python} -V")
                env = Env(pyver, python, shell)

                with change_dir(Path(proj.slug)):
                    print(f"Prepping for {proj.slug} {pyver.command}")
                    proj.prep_environment(env)
                    for cov_slug, cov_pip, cov_options in cov_versions:
                        durations = []
                        for run_num in range(num_runs):
                            print(
                                f"Running tests, cov={cov_slug}, {run_num+1} of {num_runs}"
                            )
                            if cov_pip is None:
                                dur = proj.run_no_coverage(env)
                            else:
                                dur = proj.run_with_coverage(env, cov_pip, cov_options)
                            print(f"Tests took {dur:.3f}s")
                            durations.append(dur)
                        med = statistics.median(durations)
                        print(
                            f"## Median for {pyver.command}, cov={cov_slug}: {med:.3f}s"
                        )


PERF_DIR = Path("/tmp/covperf")


print(f"Removing and re-making {PERF_DIR}")
rmrf(PERF_DIR)

with change_dir(PERF_DIR):

    run_experiments(
        py_versions=[
            Python(3, 7),
            Python(3, 10),
        ],
        cov_versions=[
            ("none", None, None),
            ("6.4", "coverage==6.4", ""),
            ("tip", "-e ~/coverage/trunk", ""),
        ],
        projects=[
            PytestHtml(),
        ],
        num_runs=5,
    )

    # run_experiments(
    #     py_versions=[
    #         PyPy(3, 9),
    #     ],
    #     cov_versions=[
    #         ("none", None, None),
    #         ("6.4", "coverage==6.4", ""),
    #         (
    #             "PR 1381",
    #             "git+https://github.com/cfbolz/coveragepy.git@f_trace_lines",
    #             "",
    #         ),
    #     ],
    #     projects=[
    #         PytestHtml(),
    #     ],
    #     num_runs=3,
    # )
