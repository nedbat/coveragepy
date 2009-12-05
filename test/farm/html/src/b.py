# A test file for HTML reporting by coverage.

def one(x):
    # This will be a branch that misses the else.
    if x < 2:
        a = 3
    else:
        a = 4

one(1)

def two(x):
    # A missed else that branches to "exit"
    if x:
        a = 5

two(1)

def three_way():
    # for-else can be a three-way branch.
    for i in range(10):
        if i == 3:
            break
    else:
        return 23
    return 17

three_way()
