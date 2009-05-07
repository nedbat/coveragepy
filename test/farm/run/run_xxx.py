copy("src", "out")
run("""
    coverage -e -x xxx
    coverage -r
    """, rundir="out", outfile="stdout.txt")
contains("out/stdout.txt", "xxx: 3 4 0 7")
doesnt_contain("out/stdout.txt", "No such file or directory")
clean("out")
