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
print(f"Comment will be: {comment}")

owner = "nedbat"
repo = "coveragepy"
for m in re.finditer(r"https://github.com/nedbat/coveragepy/(issues|pull)/(\d+)", latest["text"]):
    kind, number = m.groups()

    if kind == "issues":
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}"
        issue_data = requests.get(url).json()
        if issue_data["state"] == "closed":
            print(f"Commenting on {m[0]}")
            url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}/comments"
            resp = requests.post(url, json={"body": comment})
            print(resp)
        else:
            print(f"Still open, comment manually: {m[0]}")
    else:
        print(f"You need to manually coment on {m[0]}")
