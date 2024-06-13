from benchmark import *

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


if 0:
    # Compare two Python versions
    v1 = 10
    v2 = 11
    run_experiment(
        py_versions=[
            Python(3, v1),
            Python(3, v2),
        ],
        cov_versions=[
            Coverage("753", "coverage==7.5.3"),
        ],
        projects=[
            ProjectMashumaro(),
        ],
        rows=["cov", "proj"],
        column="pyver",
        ratios=[
            (f"3.{v2} vs 3.{v1}", f"python3.{v2}", f"python3.{v1}"),
        ],
    )

if 1:
    # Compare current Coverage source against shipped version
    run_experiment(
        py_versions=[
            Python(3, 11),
        ],
        cov_versions=[
            Coverage("pip", "coverage"),
            CoverageSource("../..", "latest"),
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
                directory="../..",
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
                directory="/Users/nbatchelder/coverage/trunk",
                env_vars={"COVERAGE_CORE": "sysmon"},
            ),
        ],
        projects=[
            ProjectMashumaro(),         # small: "-k ck"
            ProjectMashumaroBranch(),   # small: "-k ck"
        ],
        rows=["pyver", "proj"],
        column="cov",
        ratios=[
            (f"732%", "732", "nocov"),
            (f"sysmon%", "sysmon", "nocov"),
        ],
    )
