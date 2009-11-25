# A test file for HTML reporting by coverage.

def one(x):
    if x < 2:
        # Needed a < to look at HTML entities.
        a = 3
    else:
        a = 4

one(1)

def two(x):
    if x:
        a = 5
        
two(1)
