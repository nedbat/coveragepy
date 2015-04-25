copy("src", "out")
run("""
    coverage run utf8.py
    coverage annotate utf8.py
    """, rundir="out")
compare("out", "gold_encodings", "*,cover")
clean("out")
