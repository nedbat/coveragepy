copy("src", "out_multi")
run("""
    coverage -e -x multi.py
    coverage -a
    """, rundir="out_multi")
compare("out_multi", "gold_multi", "*,cover")
clean("out_multi")
