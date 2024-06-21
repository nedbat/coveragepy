.. Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
.. For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

=====================
Coverage.py Benchmark
=====================

This is an attempt at a disciplined benchmark for coverage performance.  The
goal is to run real-world test suites under controlled conditions to measure
relative performance.

We want to be able to make comparisons like:

- Is coverage under Python 3.12 faster than under 3.11?

- What is the performance overhead of coverage measurement compared to no
  coverage?

- How does sys.monitoring overhead compare to sys.settrace overhead?


Challenges:

- Real-world test suites have differing needs and differing styles of
  execution. It's hard to invoke them uniformly and get consistent execution.

- The projects might not yet run correctly on the newer versions of Python that
  we want to test.

- Projects don't have uniform ways of setting coverage options.  For example,
  we'd like to be able to run the test suite both with and without coverage
  measurement, but many projects aren't configured to make that possible.


Running
-------

The benchmark.py module defines the ``run_experiment`` function and helpers to
build its arguments.

The arguments to ``run_experiment`` specify a collection of Python versions,
coverage.py versions, and projects to run.  All the combinations form a matrix,
and are run a number of times. The timings are collected and summarized.
Finally, a Markdown table is printed.

There are three dimensions to the matrix: ``pyver``, ``cov``, and ``proj``.
The `rows` argument determines the two dimensions that will produce the rows
for the table.  There will be a row for each combination of the two dimensions.

The `column` argument is the remaining dimension that is used to add columns to
the table, one for each item in that dimension.

For example::

    run_experiment(
        py_versions=[
            Python(3, 10),
            Python(3, 11),
            Python(3, 12),
        ],
        cov_versions=[
            Coverage("753", "coverage==7.5.3"),
            CoverageSource("~/coverage"),
        ],
        projects=[
            ProjectSlow(),
            ProjectStrange(),
        ],
        rows=["cov", "proj"],
        column="pyver",
        ...
    )

This will run test suites twelve times: three Python versions times two
coverage versions on two different projects.  The coverage versions and
projects will be combined to form rows, so there will be six rows in the table.
Each row will have columns naming the coverage version and project used, and
then three more columns, one for each Python version.

The output might look like this::

    | cov    | proj   |   python3.10 |   python3.11 |   python3.12 |
    |:-------|:-------|-------------:|-------------:|-------------:|
    | 753    | slow   |        23.9s |        24.2s |        24.2s |
    | 753    | odd    |        10.1s |         9.9s |        10.1s |
    | source | slow   |        23.9s |        24.2s |        23.9s |
    | source | odd    |        10.5s |        10.5s |         9.9s |

Ratios are calculated among the columns using the `ratios` argument. It's a
list of triples: the header for the column, and the two slugs from the `column`
dimension to compare.

In our example we could have::

        ratios=[
            ("11 vs 10", "python3.11", "python3.10"),
            ("12 vs 11", "python3.12", "python3.11"),
        ],

This will add two more columns to the table, showing the 3.11 time divided by
the 3.10 time, and the 3.12 time divided by the 3.11 time::

    | cov    | proj   |   python3.10 |   python3.11 |   python3.12 |   11 vs 10 |   12 vs 11 |
    |:-------|:-------|-------------:|-------------:|-------------:|-----------:|-----------:|
    | 753    | slow   |        24.2s |        24.2s |        23.9s |       100% |        99% |
    | 753    | odd    |        10.1s |        10.5s |        10.5s |       104% |       100% |
    | source | slow   |        23.9s |        24.2s |        23.9s |       101% |        99% |
    | source | odd    |        10.1s |         9.9s |         9.9s |        98% |       100% |


Sample run
----------

If you create compare-10-11.py like this::

    # Compare two Python versions
    run_experiment(
        py_versions=[
            Python(3, 10),
            Python(3, 11),
        ],
        cov_versions=[
            Coverage("753", "coverage==7.5.3"),
        ],
        projects=[
            ProjectMashumaro(),
            ProjectOperator(),
        ],
        rows=["cov", "proj"],
        column="pyver",
        ratios=[
            ("3.11 vs 3.10", "python3.11", "python3.10"),
        ],
        num_runs=1,
    )

This produces this output::

    % python compare-10-11.py
    Removing and re-making /tmp/covperf
    Logging output to /private/tmp/covperf/output_mashumaro.log
    Prepping project mashumaro
    Making venv for mashumaro python3.10
    Prepping for mashumaro python3.10
    Making venv for mashumaro python3.11
    Prepping for mashumaro python3.11
    Logging output to /private/tmp/covperf/output_operator.log
    Prepping project operator
    Making venv for operator python3.10
    Prepping for operator python3.10
    Making venv for operator python3.11
    Prepping for operator python3.11
    Logging output to /private/tmp/covperf/output_mashumaro.log
    Running tests: proj=mashumaro, py=python3.11, cov=753, 1 of 4
    Results: TOTAL                                                                     11061     66  99.403309%
    Tests took 75.985s
    Logging output to /private/tmp/covperf/output_operator.log
    Running tests: proj=operator, py=python3.11, cov=753, 2 of 4
    Results: TOTAL                       6021    482  91.994685%
    Tests took 94.856s
    Logging output to /private/tmp/covperf/output_mashumaro.log
    Running tests: proj=mashumaro, py=python3.10, cov=753, 3 of 4
    Results: TOTAL                                                                     11061    104  99.059760%
    Tests took 77.815s
    Logging output to /private/tmp/covperf/output_operator.log
    Running tests: proj=operator, py=python3.10, cov=753, 4 of 4
    Results: TOTAL                       6021    482  91.994685%
    Tests took 108.106s
    # Results
    Median for mashumaro, python3.10, 753: 77.815s, stdev=0.000, data=77.815
    Median for mashumaro, python3.11, 753: 75.985s, stdev=0.000, data=75.985
    Median for operator, python3.10, 753: 108.106s, stdev=0.000, data=108.106
    Median for operator, python3.11, 753: 94.856s, stdev=0.000, data=94.856

    | cov   | proj      |   python3.10 |   python3.11 |   3.11 vs 3.10 |
    |:------|:----------|-------------:|-------------:|---------------:|
    | 753   | mashumaro |        77.8s |        76.0s |            98% |
    | 753   | operator  |       108.1s |        94.9s |            88% |
