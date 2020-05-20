#!/usr/bin/env python3
"""
Upload release notes into GitHub releases.
"""

import json
import shlex
import subprocess
import sys

import pkg_resources
import requests


RELEASES_URL = "https://api.github.com/repos/{repo}/releases"

def run_command(cmd):
    """
    Run a command line (with no shell).

    Returns a tuple:
        bool: true if the command succeeded.
        str: the output of the command.

    """
    proc = subprocess.run(
        shlex.split(cmd),
        shell=False,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    output = proc.stdout.decode("utf-8")
    succeeded = proc.returncode == 0
    return succeeded, output

def does_tag_exist(tag_name):
    """
    Does `tag_name` exist as a tag in git?
    """
    return run_command(f"git rev-parse --verify {tag_name}")[0]

def check_ok(resp):
    """
    Check that the Requests response object was successful.

    Raise an exception if not.
    """
    if not resp:
        print(f"text: {resp.text!r}")
        resp.raise_for_status()

def github_paginated(session, url):
    """
    Get all the results from a paginated GitHub url.
    """
    while True:
        resp = session.get(url)
        check_ok(resp)
        yield from resp.json()
        next_link = resp.links.get("next", None)
        if not next_link:
            break
        url = next_link["url"]

def get_releases(session, repo):
    """
    Get all the releases from a name/project repo.

    Returns:
        A dict mapping tag names to release dictionaries.
    """
    url = RELEASES_URL.format(repo=repo)
    releases = { r['tag_name']: r for r in github_paginated(session, url) }
    return releases

def release_for_relnote(relnote):
    """
    Turn a release note dict into the data needed by GitHub for a release.
    """
    tag = f"coverage-{relnote['version']}"
    return {
        "tag_name": tag,
        "name": tag,
        "body": relnote["text"],
        "draft": False,
        "prerelease": relnote["prerelease"],
    }

def create_release(session, repo, relnote):
    """
    Create a new GitHub release.
    """
    print(f"Creating {relnote['version']}")
    data = release_for_relnote(relnote)
    resp = session.post(RELEASES_URL.format(repo=repo), json=data)
    check_ok(resp)

def update_release(session, url, relnote):
    """
    Update an existing GitHub release.
    """
    print(f"Updating {relnote['version']}")
    data = release_for_relnote(relnote)
    resp = session.patch(url, json=data)
    check_ok(resp)

def update_github_releases(json_filename, repo):
    """
    Read the json file, and create or update releases in GitHub.
    """
    gh_session = requests.Session()
    releases = get_releases(gh_session, repo)
    if 0:   # if you need to delete all the releases!
        for release in releases.values():
            print(release["tag_name"])
            resp = gh_session.delete(release["url"])
            check_ok(resp)
        return

    with open(json_filename) as jf:
        relnotes = json.load(jf)
    relnotes.sort(key=lambda rel: pkg_resources.parse_version(rel["version"]))
    for relnote in relnotes:
        tag = "coverage-" + relnote["version"]
        if not does_tag_exist(tag):
            continue
        exists = tag in releases
        if not exists:
            create_release(gh_session, repo, relnote)
        else:
            release = releases[tag]
            if release["body"] != relnote["text"]:
                url = release["url"]
                update_release(gh_session, url, relnote)

if __name__ == "__main__":
    update_github_releases(*sys.argv[1:])   # pylint: disable=no-value-for-parameter
