copy("src", "out")
run("""
    coverage -x white.py
    coverage -a white.py
    """, rundir="out")
compare("out", "gold", "*,cover")
clean("out")
