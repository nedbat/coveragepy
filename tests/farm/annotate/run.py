# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

copy("src", "out")
run("""
    coverage run white.py
    coverage annotate white.py
    """, rundir="out")
compare("out", "gold", "*,cover")
clean("out")
