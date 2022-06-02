# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Add a release comment to all the issues mentioned in the latest release."""

import json
import re
import sys

import requests

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
for m in re.finditer(rf"https://github.com/{repo_owner}/(issues|pull)/(\d+)", latest["text"]):
    kind, number = m.groups()
    do_comment = False

    if kind == "issues":
        url = f"https://api.github.com/repos/{repo_owner}/issues/{number}"
        issue_data = requests.get(url).json()
        if issue_data["state"] == "closed":
            do_comment = True
        else:
            print(f"Still open, comment manually: {m[0]}")
    else:
        url = f"https://api.github.com/repos/{repo_owner}/pulls/{number}"
        pull_data = requests.get(url).json()
        if pull_data["state"] == "closed":
            if pull_data["merged"]:
                do_comment = True
            else:
                print(f"Not merged, comment manually: {m[0]}")
        else:
            print(f"Still open, comment manually: {m[0]}")

    if do_comment:
        print(f"Commenting on {m[0]}")
        url = f"https://api.github.com/repos/{repo_owner}/issues/{number}/comments"
        resp = requests.post(url, json={"body": comment})
        print(resp)
