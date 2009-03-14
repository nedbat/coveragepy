clean("src", "*,cover")
run("""
    coverage -x white.py
    coverage -a white.py
    """)
compare("src", "gold", "*,cover")
clean("src", "*,cover")
