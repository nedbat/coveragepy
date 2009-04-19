copy("src", "out")
run("""
    coverage -e -x white.py
    coverage -a white.py
    """, rundir="out")
compare("out", "gold", "*,cover")
clean("out")
