# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Help make a requests Session with proper authentication."""

import os
import sys

import requests

_SESSION = None

def get_session():
    """Get a properly authenticated requests Session."""

    global _SESSION

    if _SESSION is None:
        # If GITHUB_TOKEN is in the environment, use it.
        token = os.environ.get("GITHUB_TOKEN")
        if token is None:
            sys.exit("!! Must have a GITHUB_TOKEN")

        _SESSION = requests.session()
        _SESSION.headers["Authorization"] = f"token {token}"
        # requests.get() will always prefer the .netrc file even if a header
        # is already set.  This tells it to ignore the .netrc file.
        _SESSION.trust_env = False

    return _SESSION
