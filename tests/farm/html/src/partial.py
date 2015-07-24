# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

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
