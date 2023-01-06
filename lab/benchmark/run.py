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


if 1:
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
