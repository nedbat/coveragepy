# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Use the GitHub API to download built artifacts."""

import datetime
import json
import os
import os.path
import sys
import time
import zipfile

import requests

def download_url(url, filename):
    """Download a file from `url` to `filename`."""
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(filename, "wb") as f:
            for chunk in response.iter_content(16*1024):
                f.write(chunk)
    else:
        raise Exception(f"Fetching {url} produced: status={response.status_code}")

def unpack_zipfile(filename):
    """Unpack a zipfile, using the names in the zip."""
    with open(filename, "rb") as fzip:
        z = zipfile.ZipFile(fzip)
        for name in z.namelist():
            print(f"  extracting {name}")
            z.extract(name)

def utc2local(timestring):
    """Convert a UTC time into local time in a more readable form.

    For example: '20201208T122900Z' to '2020-12-08 07:29:00'.

    """
    dt = datetime.datetime
    utc = dt.fromisoformat(timestring.rstrip("Z"))
    epoch = time.mktime(utc.timetuple())
    offset = dt.fromtimestamp(epoch) - dt.utcfromtimestamp(epoch)
    local = utc + offset
    return local.strftime("%Y-%m-%d %H:%M:%S")

dest = "dist"
repo_owner = sys.argv[1]
temp_zip = "artifacts.zip"

os.makedirs(dest, exist_ok=True)
os.chdir(dest)

r = requests.get(f"https://api.github.com/repos/{repo_owner}/actions/artifacts")
if r.status_code == 200:
    dists = [a for a in r.json()["artifacts"] if a["name"] == "dist"]
    if not dists:
        print("No recent dists!")
    else:
        latest = max(dists, key=lambda a: a["created_at"])
        print(f"Artifacts created at {utc2local(latest['created_at'])}")
        download_url(latest["archive_download_url"], temp_zip)
        unpack_zipfile(temp_zip)
        os.remove(temp_zip)
else:
    print(f"Fetching artifacts returned status {r.status_code}:")
    print(json.dumps(r.json(), indent=4))
    sys.exit(1)
