# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

copy("src", "out")
run("""
    coverage run chdir.py
    coverage report
    """, rundir="out", outfile="stdout.txt")
contains("out/stdout.txt",
        "Line One",
        "Line Two",
        "chdir"
        )
doesnt_contain("out/stdout.txt", "No such file or directory")
clean("out")
