copy("src", "out")
run("""
    coverage run chdir.py
    coverage -r
    """, rundir="out", outfile="stdout.txt")
contains("out/stdout.txt",
        "Line One",
        "Line Two",
        "chdir"
        )
doesnt_contain("out/stdout.txt", "No such file or directory")
clean("out")
