# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

copy("src", "out_multi")
run("""
    coverage run multi.py
    coverage annotate
    """, rundir="out_multi")
compare("out_multi", "gold_multi", "*,cover")
clean("out_multi")
