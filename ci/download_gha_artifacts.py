# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Use the GitHub API to download built artifacts."""

import collections
import datetime
import fnmatch
import operator
import os
import os.path
import sys
import time
import zipfile

from session import get_session

def download_url(url, filename):
    """Download a file from `url` to `filename`."""
    response = get_session().get(url, stream=True)
    if response.status_code == 200:
        with open(filename, "wb") as f:
            for chunk in response.iter_content(16*1024):
                f.write(chunk)
    else:
        raise RuntimeError(f"Fetching {url} produced: status={response.status_code}")


def unpack_zipfile(filename):
    """Unpack a zipfile, using the names in the zip."""
    with open(filename, "rb") as fzip:
        z = zipfile.ZipFile(fzip)
        for name in z.namelist():
            print(f"  extracting {name}")
            z.extract(name)


def utc2local(timestring):
    """
    Convert a UTC time into local time in a more readable form.

    For example: '20201208T122900Z' to '2020-12-08 07:29:00'.

    """
    dt = datetime.datetime
    utc = dt.fromisoformat(timestring.rstrip("Z"))
    epoch = time.mktime(utc.timetuple())
    offset = dt.fromtimestamp(epoch) - dt.utcfromtimestamp(epoch)
    local = utc + offset
    return local.strftime("%Y-%m-%d %H:%M:%S")


def all_items(url, key):
    """
    Get all items from a paginated GitHub URL.

    `key` is the key in the top-level returned object that has a list of items.

    """
    url += ("&" if "?" in url else "?") + "per_page=100"
    while url:
        response = get_session().get(url)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and (msg := data.get("message")):
            raise RuntimeError(f"URL {url!r} failed: {msg}")
        yield from data.get(key, ())
        try:
            url = response.links.get("next").get("url")
        except AttributeError:
            url = None


def main(owner_repo, artifact_pattern, dest_dir):
    """
    Download and unzip the latest artifacts matching a pattern.

    `owner_repo` is a GitHub pair for the repo, like "nedbat/coveragepy".
    `artifact_pattern` is a filename glob for the artifact name.
    `dest_dir` is the directory to unpack them into.

    """
    # Get all artifacts matching the pattern, grouped by name.
    url = f"https://api.github.com/repos/{owner_repo}/actions/artifacts"
    artifacts_by_name = collections.defaultdict(list)
    for artifact in all_items(url, "artifacts"):
        name = artifact["name"]
        if not fnmatch.fnmatch(name, artifact_pattern):
            continue
        artifacts_by_name[name].append(artifact)

    os.makedirs(dest_dir, exist_ok=True)
    os.chdir(dest_dir)
    temp_zip = "artifacts.zip"

    # Download the latest of each name.
    for name, artifacts in artifacts_by_name.items():
        artifact = max(artifacts, key=operator.itemgetter("created_at"))
        print(
            f"Downloading {artifact['name']}, "
            + f"size: {artifact['size_in_bytes']}, "
            + f"created: {utc2local(artifact['created_at'])}"
        )
        download_url(artifact["archive_download_url"], temp_zip)
        unpack_zipfile(temp_zip)
        os.remove(temp_zip)


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
