#!/usr/bin/env python3
"""
Upload release notes from a JSON file to Tidelift as Markdown chunks

Put your Tidelift API token in a file called tidelift.token alongside this
program, for example:

    user/n3IwOpxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxc2ZwE4

Run with two arguments: the JSON file of release notes, and the Tidelift
package name:

	python tidelift_relnotes.py relnotes.json pypi/coverage

Every section that has something that looks like a version number in it will
be uploaded as the release notes for that version.

"""

import json
import os.path
import sys

import requests


def update_release_note(package, version, text):
    """Update the release notes for one version of a package."""
    url = f"https://api.tidelift.com/external-api/lifting/{package}/release-notes/{version}"
    token_file = os.path.join(os.path.dirname(__file__), "tidelift.token")
    with open(token_file) as ftoken:
        token = ftoken.read().strip()
    headers = {
        "Authorization": f"Bearer: {token}",
    }
    req_args = dict(url=url, data=text.encode('utf8'), headers=headers)
    result = requests.post(**req_args)
    if result.status_code == 409:
        result = requests.put(**req_args)
    print(f"{version}: {result.status_code}")

def upload(json_filename, package):
    """Main function: parse markdown and upload to Tidelift."""
    with open(json_filename) as jf:
        relnotes = json.load(jf)
    for relnote in relnotes:
        update_release_note(package, relnote["version"], relnote["text"])

if __name__ == "__main__":
    upload(*sys.argv[1:])           # pylint: disable=no-value-for-parameter
