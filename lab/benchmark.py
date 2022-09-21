"""Run performance comparisons for versions of coverage"""

import contextlib
import dataclasses
import itertools
import os
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

from typing import Dict, Iterable, Iterator, List, Optional, Tuple


class ShellSession:
    """A logged shell session.

    The duration of the last command is available as .last_duration.
    """

    def __init__(self, output_filename: str):
        self.output_filename = output_filename
        self.last_duration: float = 0
        self.foutput = None

    def __enter__(self):
        self.foutput = open(self.output_filename, "a", encoding="utf-8")
        print(f"Logging output to {os.path.abspath(self.output_filename)}")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.foutput.close()

    def print(self, *args, **kwargs):
        """Print a message to this shell's log."""
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
        if self.git_url:
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
        """Run a tox command. Return the duration."""
        env.shell.run_command(f"{env.python} -m tox -e {toxenv} {toxargs}")
        return env.shell.last_duration

    def run_no_coverage(self, env):
        return self.run_tox(env, env.pyver.toxenv, "--skip-pkg-install")

    def run_with_coverage(self, env, pip_args, cov_options):
        assert not cov_options, f"ToxProject.run_with_coverage can't take cov_options={cov_options!r}"
        self.run_tox(env, env.pyver.toxenv, "--notest")
        env.shell.run_command(
            f".tox/{env.pyver.toxenv}/bin/python -m pip install {pip_args}"
        )
        return self.run_tox(env, env.pyver.toxenv, "--skip-pkg-install")


class ProjectPytestHtml(ToxProject):
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

    def run_with_coverage(self, env, pip_args, cov_options):
        env.shell.run_command(f"{env.python} -m pip install {pip_args}")
        with change_dir(self.cur_dir):
            env.shell.run_command(
                f"{env.python} -m coverage run {self.python_file}"
            )
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
        self.slug = slug
        self.toxenv = None

@dataclasses.dataclass
class Coverage:
    """A version of coverage.py to use, maybe None."""
    # Short word for messages, directories, etc
    slug: str
    # Arguments for "pip install ..."
    pip_args: Optional[str] = None
    # Tweaks to the .coveragerc file
    options: Optional[str] = None

class CoveragePR(Coverage):
    """A version of coverage.py from a pull request."""
    def __init__(self, number, options=None):
        super().__init__(
            slug=f"#{number}",
            pip_args=f"git+https://github.com/nedbat/coveragepy.git@refs/pull/{number}/merge",
            options=options,
        )

class CoverageCommit(Coverage):
    """A version of coverage.py from a specific commit."""
    def __init__(self, sha, options=None):
        super().__init__(
            slug=sha,
            pip_args=f"git+https://github.com/nedbat/coveragepy.git@{sha}",
            options=options,
        )

class CoverageSource(Coverage):
    """The coverage.py in a working tree."""
    def __init__(self, directory, options=None):
        super().__init__(
            slug="source",
            pip_args=directory,
            options=options,
        )


@dataclasses.dataclass
class Env:
    """An environment to run a test suite in."""

    pyver: PyVersion
    python: Path
    shell: ShellSession


ResultData = Dict[Tuple[str, str, str], float]

class Experiment:
    """A particular time experiment to run."""

    def __init__(
        self,
        py_versions: List[PyVersion],
        cov_versions: List[Coverage],
        projects: List[ProjectToTest],
    ):
        self.py_versions = py_versions
        self.cov_versions = cov_versions
        self.projects = projects
        self.result_data: ResultData = {}

    def run(self, num_runs: int = 3) -> None:
        results = []
        for proj in self.projects:
            print(f"Testing with {proj.slug}")
            with ShellSession(f"output_{proj.slug}.log") as shell:
                proj.get_source(shell)

                for pyver in self.py_versions:
                    print(f"Making venv for {proj.slug} {pyver.slug}")
                    venv_dir = f"venv_{proj.slug}_{pyver.slug}"
                    shell.run_command(f"{pyver.command} -m venv {venv_dir}")
                    python = Path.cwd() / f"{venv_dir}/bin/python"
                    shell.run_command(f"{python} -V")
                    env = Env(pyver, python, shell)

                    with change_dir(Path(proj.slug)):
                        print(f"Prepping for {proj.slug} {pyver.slug}")
                        proj.prep_environment(env)
                        for cov_ver in self.cov_versions:
                            durations = []
                            for run_num in range(num_runs):
                                print(
                                    f"Running tests, cov={cov_ver.slug}, {run_num+1} of {num_runs}"
                                )
                                if cov_ver.pip_args is None:
                                    dur = proj.run_no_coverage(env)
                                else:
                                    dur = proj.run_with_coverage(
                                        env, cov_ver.pip_args, cov_ver.options,
                                    )
                                print(f"Tests took {dur:.3f}s")
                                durations.append(dur)
                            med = statistics.median(durations)
                            result = (
                                f"Median for {proj.slug}, {pyver.slug}, "
                                + f"cov={cov_ver.slug}: {med:.3f}s"
                            )
                            print(f"## {result}")
                            results.append(result)
                            result_key = (proj.slug, pyver.slug, cov_ver.slug)
                            self.result_data[result_key] = med

        print("# Results")
        for result in results:
            print(result)

    def show_results(
        self,
        rows: List[str],
        column: str,
        ratios: Iterable[Tuple[str, str, str]] = (),
    ) -> None:
        dimensions = {
            "cov": [cov_ver.slug for cov_ver in self.cov_versions],
            "pyver": [pyver.slug for pyver in self.py_versions],
            "proj": [proj.slug for proj in self.projects],
        }

        table_axes = [dimensions[rowname] for rowname in rows]
        data_order = [*rows, column]
        remap = [data_order.index(datum) for datum in ["proj", "pyver", "cov"]]

        WIDTH = 20
        def as_table_row(vals):
            return "| " + " | ".join(v.ljust(WIDTH) for v in vals) + " |"

        header = []
        header.extend(rows)
        header.extend(dimensions[column])
        header.extend(slug for slug, _, _ in ratios)

        print()
        print(as_table_row(header))
        dashes = [":---"] * len(rows) + ["---:"] * (len(header) - len(rows))
        print(as_table_row(dashes))
        for tup in itertools.product(*table_axes):
            row = []
            row.extend(tup)
            col_data = {}
            for col in dimensions[column]:
                key = (*tup, col)
                key = tuple(key[i] for i in remap)
                result_time = self.result_data[key]     # type: ignore
                row.append(f"{result_time:.3f} s")
                col_data[col] = result_time
            for _, num, denom in ratios:
                ratio = col_data[num] / col_data[denom]
                row.append(f"{ratio * 100:.2f}%")
            print(as_table_row(row))


PERF_DIR = Path("/tmp/covperf")

def run_experiment(
    py_versions: List[PyVersion], cov_versions: List[Coverage], projects: List[ProjectToTest],
    rows: List[str], column: str, ratios: Iterable[Tuple[str, str, str]] = (),
):
    slugs = [v.slug for v in py_versions + cov_versions + projects]
    if len(set(slugs)) != len(slugs):
        raise Exception(f"Slugs must be unique: {slugs}")
    if any(" " in slug for slug in slugs):
        raise Exception(f"No spaces in slugs please: {slugs}")
    ratio_slugs = [rslug for ratio in ratios for rslug in ratio[1:]]
    if any(rslug not in slugs for rslug in ratio_slugs):
        raise Exception(f"Ratio slug doesn't match a slug: {ratio_slugs}, {slugs}")

    print(f"Removing and re-making {PERF_DIR}")
    rmrf(PERF_DIR)

    with change_dir(PERF_DIR):
        exp = Experiment(py_versions=py_versions, cov_versions=cov_versions, projects=projects)
        exp.run(num_runs=int(sys.argv[1]))
        exp.show_results(rows=rows, column=column, ratios=ratios)


if 1:
    run_experiment(
        py_versions=[
            #Python(3, 11),
            AdHocPython("/usr/local/cpython/v3.10.5", "v3.10.5"),
            AdHocPython("/usr/local/cpython/v3.11.0b3", "v3.11.0b3"),
            AdHocPython("/usr/local/cpython/94231", "94231"),
        ],
        cov_versions=[
            Coverage("6.4.1", "coverage==6.4.1"),
        ],
        projects=[
            AdHocProject("/src/bugs/bug1339/bug1339.py"),
            SlipcoverBenchmark("bm_sudoku.py"),
            SlipcoverBenchmark("bm_spectral_norm.py"),
        ],
        rows=["cov", "proj"],
        column="pyver",
        ratios=[
            ("3.11b3 vs 3.10", "v3.11.0b3", "v3.10.5"),
            ("94231 vs 3.10", "94231", "v3.10.5"),
        ],
    )
