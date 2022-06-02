"""Add a release comment to all the issues mentioned in the latest release."""

import json
import re

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

owner = "nedbat"
repo = "coveragepy"
for m in re.finditer(rf"https://github.com/{owner}/{repo}/(issues|pull)/(\d+)", latest["text"]):
    kind, number = m.groups()
    do_comment = False

    if kind == "issues":
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}"
        issue_data = requests.get(url).json()
        if issue_data["state"] == "closed":
            do_comment = True
        else:
            print(f"Still open, comment manually: {m[0]}")
    else:
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
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
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}/comments"
        resp = requests.post(url, json={"body": comment})
        print(resp)
