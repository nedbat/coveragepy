from benchmark import *

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
        EmptyProject("empty", [1.2, 3.4]),
        EmptyProject("dummy", [6.9, 7.1]),
    ],
    rows=["proj", "pyver"],
    column="cov",
    ratios=[
        (".2 vs .1", "702", "701"),
        (".1 dynctx cost", "701.dynctx", "701"),
        (".2 dynctx cost", "702.dynctx", "702"),
    ],
)
