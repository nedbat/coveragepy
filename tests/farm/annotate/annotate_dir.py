# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

copy("src", "run")
run("""
    coverage run multi.py
    coverage annotate -d out_anno_dir
    """, rundir="run")
compare("gold_anno_dir", "run/out_anno_dir", "*,cover", actual_extra=True)
clean("run")
