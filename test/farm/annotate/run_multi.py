outdir = "out_multi"
copy("src", outdir)
run("""
    coverage -x multi.py
    coverage -a 
    """, rundir=outdir)
compare(outdir, "gold_multi", "*,cover")
clean(outdir)
