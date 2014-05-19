copy("src", "out")
run("""
    coverage run white.py
    coverage annotate white.py
    """, rundir="out")
compare("out", "gold", "*,cover")
clean("out")
