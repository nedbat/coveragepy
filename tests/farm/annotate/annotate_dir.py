copy("src", "run")
run("""
    coverage run multi.py
    coverage annotate -d out_anno_dir
    """, rundir="run")
compare("run/out_anno_dir", "gold_anno_dir", "*,cover", left_extra=True)
clean("run")
