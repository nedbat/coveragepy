copy("src", "out_multi")
run("""
    coverage run multi.py
    coverage annotate
    """, rundir="out_multi")
compare("out_multi", "gold_multi", "*,cover")
clean("out_multi")
