from benchmark import *

class ProjectSlow(EmptyProject):
    def __init__(self):
        super().__init__(slug="slow", fake_durations=[23.9, 24.2])

class ProjectOdd(EmptyProject):
    def __init__(self):
        super().__init__(slug="odd", fake_durations=[10.1, 10.5, 9.9])


run_experiment(
    py_versions=[
        Python(3, 10),
        Python(3, 11),
    #    Python(3, 12),
    ],
    cov_versions=[
        Coverage("753", "coverage==7.5.3"),
        CoverageSource("~/coverage"),
    ],
    projects=[
        ProjectSlow(),
        ProjectOdd(),
    ],
    rows=["cov", "proj"],
    column="pyver",
    ratios=[
        ("11 vs 10", "python3.11", "python3.10"),
    #    ("12 vs 11", "python3.12", "python3.11"),
    ],
)
