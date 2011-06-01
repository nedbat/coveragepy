# partial branches

a = 3

while True:
    break

while 1:
    break

while a:        # pragma: no branch
    break

if 0:
    never_happen()

if 1:
    a = 13

