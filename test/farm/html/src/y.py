# A test file for XML reporting by coverage.

def choice(x):
    if x < 2:
        return 3
    else:
        return 4

assert choice(1) == 3
