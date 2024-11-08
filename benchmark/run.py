import optparse
from pathlib import Path

from benchmark import *

parser = optparse.OptionParser()
parser.add_option(
    "--clean",
    action="store_true",
    dest="clean",
    default=False,
    help="Delete the results.json file before running benchmarks"
)
options, args = parser.parse_args()

if options.clean:
    results_file = Path("results.json")
    if results_file.exists():
        results_file.unlink()
        print("Deleted results.json")

if 0:
    run_experiment(
        py_versions=[
            # Python(3, 11),
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


if 0:
    run_experiment(
        py_versions=[
            Python(3, 9),
            Python(3, 11),
        ],
        cov_versions=[
            Coverage("701", "coverage==7.0.1"),
            Coverage(
                "701.dynctx", "coverage==7.0.1", [("dynamic_context", "test_function")]
            ),
            Coverage("702", "coverage==7.0.2"),
            Coverage(
                "702.dynctx", "coverage==7.0.2", [("dynamic_context", "test_function")]
            ),
        ],
        projects=[
            ProjectAttrs(),
        ],
        rows=["proj", "pyver"],
        column="cov",
        ratios=[
            (".2 vs .1", "702", "701"),
            (".1 dynctx cost", "701.dynctx", "701"),
            (".2 dynctx cost", "702.dynctx", "702"),
        ],
    )

if 1:
    # Compare N Python versions
    vers = [10, 11, 12, 13]
    run_experiment(
        py_versions=[Python(3, v) for v in vers],
        cov_versions=[
            Coverage("761", "coverage==7.6.1"),
        ],
        projects=[
            ProjectMashumaro(),
            ProjectPygments(),
            ProjectMypy(),
        ],
        rows=["cov", "proj"],
        column="pyver",
        ratios=[
            (f"3.{b} vs 3.{a}", f"python3.{b}", f"python3.{a}")
            for a, b in zip(vers, vers[1:])
        ],
    )

if 0:
    # Compare sysmon on many projects

    run_experiment(
        py_versions=[
            Python(3, 12),
        ],
        cov_versions=[
            NoCoverage("nocov"),
            CoverageSource(slug="ctrace", env_vars={"COVERAGE_CORE": "ctrace"}),
            CoverageSource(slug="sysmon", env_vars={"COVERAGE_CORE": "sysmon"}),
        ],
        projects=[
            # ProjectSphinx(),  # Works, slow
            ProjectPygments(),  # Works
            # ProjectRich(),  # Doesn't work
            # ProjectTornado(),  # Works, tests fail
            # ProjectDulwich(),  # Works
            # ProjectBlack(),  # Works, slow
            # ProjectMpmath(),  # Works, slow
            ProjectMypy(),  # Works, slow
            # ProjectHtml5lib(),  # Works
            # ProjectUrllib3(),  # Works
        ],
        rows=["pyver", "proj"],
        column="cov",
        ratios=[
            (f"ctrace%", "ctrace", "nocov"),
            (f"sysmon%", "sysmon", "nocov"),
        ],
        load=True,
    )

if 0:
    # Compare current Coverage source against shipped version
    run_experiment(
        py_versions=[
            Python(3, 11),
        ],
        cov_versions=[
            Coverage("pip", "coverage"),
            CoverageSource(slug="latest"),
        ],
        projects=[
            ProjectMashumaro(),
            ProjectOperator(),
        ],
        rows=["pyver", "proj"],
        column="cov",
        ratios=[
            (f"Latest vs shipped", "latest", "pip"),
        ],
    )

if 0:
    # Compare 3.12 coverage vs no coverage
    run_experiment(
        py_versions=[
            Python(3, 12),
        ],
        cov_versions=[
            NoCoverage("nocov"),
            Coverage("732", "coverage==7.3.2"),
            CoverageSource(
                slug="sysmon",
                env_vars={"COVERAGE_CORE": "sysmon"},
            ),
        ],
        projects=[
            ProjectMashumaro(),     # small: "-k ck"
            ProjectOperator(),      # small: "-k irk"
        ],
        rows=["pyver", "proj"],
        column="cov",
        ratios=[
            (f"732%", "732", "nocov"),
            (f"sysmon%", "sysmon", "nocov"),
        ],
    )
