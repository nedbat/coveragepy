# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Trigger a repository_dispatch GitHub action."""

import sys

from session import get_session

repo_owner, event_type = sys.argv[1:]

# The GitHub URL makes no mention of which workflow to use. It's found based on
# the event_type, which matches the types in the workflow:
#
#   on:
#     repository_dispatch:
#       types:
#         - build-kits
#

url = f"https://api.github.com/repos/{repo_owner}/dispatches"
data = {"event_type": event_type}

resp = get_session().post(url, json=data)
if resp.status_code // 100 == 2:
    print("Success")
else:
    print(f"Status: {resp.status_code}")
    print(resp.text)
