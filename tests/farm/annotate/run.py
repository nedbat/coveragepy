# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

copy("src", "out")
run("""
    coverage run white.py
    coverage annotate white.py
    """, rundir="out")
compare("out", "gold", "*,cover")
clean("out")
