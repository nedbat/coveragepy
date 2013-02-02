copy("src", "run")
run("""
    coverage -e -x multi.py
    coverage -a -d out_anno_dir
    """, rundir="run")
compare("run/out_anno_dir", "gold_anno_dir", "*,cover", left_extra=True)
clean("run")
