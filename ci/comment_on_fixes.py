# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Add a release comment to all the issues mentioned in the latest release."""

import json
import re
import sys

from session import get_session

with open("tmp/relnotes.json") as frn:
    relnotes = json.load(frn)

latest = relnotes[0]
version = latest["version"]
comment = (
    f"This is now released as part of [coverage {version}]" +
    f"(https://pypi.org/project/coverage/{version})."
)
print(f"Comment will be:\n\n{comment}\n")

repo_owner = sys.argv[1]
url_matches = re.finditer(fr"https://github.com/{repo_owner}/(issues|pull)/(\d+)", latest["text"])
urls = set((m[0], m[1], m[2]) for m in url_matches)

for url, kind, number in urls:
    do_comment = False

    if kind == "issues":
        url = f"https://api.github.com/repos/{repo_owner}/issues/{number}"
        issue_data = get_session().get(url).json()
        if issue_data["state"] == "closed":
            do_comment = True
        else:
            print(f"Still open, comment manually: {url}")
    else:
        url = f"https://api.github.com/repos/{repo_owner}/pulls/{number}"
        pull_data = get_session().get(url).json()
        if pull_data["state"] == "closed":
            if pull_data["merged"]:
                do_comment = True
            else:
                print(f"Not merged, comment manually: {url}")
        else:
            print(f"Still open, comment manually: {url}")

    if do_comment:
        print(f"Commenting on {url}")
        url = f"https://api.github.com/repos/{repo_owner}/issues/{number}/comments"
        resp = get_session().post(url, json={"body": comment})
        print(resp)
