# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

copy("src", "out")
run("""
    coverage run utf8.py
    coverage annotate utf8.py
    """, rundir="out")
compare("out", "gold_encodings", "*,cover")
clean("out")
