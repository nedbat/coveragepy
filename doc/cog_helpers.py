# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""
Functions for use with cog in the documentation.
"""

import os
import re
import textwrap

import cog              # pylint: disable=import-error

from coverage.config import read_coverage_config

def _read_config(text, fname):
    """
    Prep and read configuration text.

    Returns the prepared text, and a dict of the settings.
    """
    # Text will be triple-quoted with an initial ignored newline.
    assert text[0] == "\n"
    text = textwrap.dedent(text[1:])

    os.makedirs("tmp", exist_ok=True)
    with open(f"tmp/{fname}", "w") as f:
        f.write(text)

    config = read_coverage_config(f"tmp/{fname}", warn=cog.error)

    values = {}
    for name, val in vars(config).items():
        if name.startswith("_"):
            continue
        if "config_file" in name:
            continue
        values[name] = val
    return text, values


def show_configs(rc, toml):
    """
    Show configuration text in a tabbed box.

    `rc` is the ini-file syntax, `toml` is the equivalent TOML syntax.
    The equivalence is checked for accuracy, and the process fails if there's
    a mismtach.

    A three-tabbed box will be produced.
    """
    rc, rc_vals = _read_config(rc, "covrc")
    toml, toml_vals = _read_config(toml, "covrc.toml")
    for key, val in rc_vals.items():
        if val != toml_vals[key]:
            cog.error(f"Mismatch! {key}: {val!r} vs {toml_vals[key]!r}")

    ini = re.sub(r"(?m)^\[", "[coverage:", rc)
    print()
    print(".. tabs::\n")
    for name, syntax, text in [
        (".coveragerc", "ini", rc),
        ("pyproject.toml", "toml", toml),
        ("setup.cfg, tox.ini", "ini", ini),
    ]:
        print(f"    .. code-tab:: {syntax}")
        print(f"        :caption: {name}")
        print()
        print(textwrap.indent(text, " " * 8))
