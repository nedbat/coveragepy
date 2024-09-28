# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Upload release notes into GitHub releases."""

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

RELEASE_BODY_FMT = """\
{relnote_text}

:arrow_right:\xa0 PyPI page: [coverage {version}](https://pypi.org/project/coverage/{version}).
:arrow_right:\xa0 To install: `python3 -m pip install coverage=={version}`
"""

def release_for_relnote(relnote):
    """
    Turn a release note dict into the data needed by GitHub for a release.
    """
    relnote_text = relnote["text"]
    tag = version = relnote["version"]
    body = RELEASE_BODY_FMT.format(relnote_text=relnote_text, version=version)
    return {
        "tag_name": tag,
        "name": version,
        "body": body,
        "draft": False,
        "prerelease": relnote["prerelease"],
    }

def create_release(session, repo, release_data):
    """
    Create a new GitHub release.
    """
    print(f"Creating {release_data['name']}")
    resp = session.post(RELEASES_URL.format(repo=repo), json=release_data)
    check_ok(resp)

def update_release(session, url, release_data):
    """
    Update an existing GitHub release.
    """
    print(f"Updating {release_data['name']}")
    resp = session.patch(url, json=release_data)
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
        tag = relnote["version"]
        if not does_tag_exist(tag):
            continue
        release_data = release_for_relnote(relnote)
        exists = tag in releases
        if not exists:
            create_release(gh_session, repo, release_data)
        else:
            release = releases[tag]
            if release["body"] != release_data["body"]:
                url = release["url"]
                update_release(gh_session, url, release_data)

if __name__ == "__main__":
    update_github_releases(*sys.argv[1:3])
