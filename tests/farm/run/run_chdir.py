# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

copy("src", "out_chdir")
run("""
    coverage run chdir.py
    coverage report
    """, rundir="out_chdir", outfile="stdout.txt")
contains("out_chdir/stdout.txt",
        "Line One",
        "Line Two",
        "chdir"
        )
doesnt_contain("out_chdir/stdout.txt", "No such file or directory")
clean("out_chdir")
