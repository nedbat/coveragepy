#!/usr/bin/env python3
"""
Upload CHANGES.rst to Tidelift as Markdown chunks
"""

import re
import subprocess

import requests

class Buffer:
    def __init__(self):
        self.buffer = []

    def append(self, text):
        self.buffer.append(text)

    def clear(self):
        self.buffer = []

    def flush(self):
        buffered = "".join(self.buffer).strip()
        if buffered:
            yield ("text", buffered)
        self.clear()


def parse_md(lines):
    buffer = Buffer()

    for line in lines:
        header_match = re.search(r"^(#+) (.+)$", line)
        is_header = bool(header_match)
        if is_header:
            yield from buffer.flush()
            hashes, text = header_match.groups()
            yield (f"h{len(hashes)}", text)
        else:
            buffer.append(line)
    yield from buffer.flush()


def sections(parsed_data):
    """Convert a stream of parsed tokens into sections with text and notes.

    Yields a stream of:
        ('h-level', 'header text', 'text')

    """
    header = None
    text = []
    for ttype, ttext in parsed_data:
        if ttype.startswith('h'):
            if header:
                yield (*header, "\n".join(text))
            text = []
            notes = []
            header = (ttype, ttext)
        elif ttype == "text":
            text.append(ttext)
        else:
            raise Exception(f"Don't know ttype {ttype!r}")
    yield (*header, "\n".join(text))


def relnotes(mdlines):
    for hlevel, htext, text in sections(parse_md(mdlines)):
        if hlevel == 'h2' and htext.startswith('Version '):
            version = htext.split()[1]
            yield version, text

def convert_rst_file_to_markdown(rst_filename):
    markdown = subprocess.check_output(["pandoc", "-frst", "-tmarkdown_strict", "--atx-headers", rst_filename])
    return markdown.decode("utf8")

def update_release_note(package, version, text):
    url = f"https://api.tidelift.com/external-api/lifting/{package}/release-notes/{version}"
    with open("ci/tidelift.token") as ftoken:
        token = ftoken.read().strip()
    headers = {
        "Authorization": f"Bearer: {token}",
    }
    req_args = dict(url=url, data=text.encode('utf8'), headers=headers)
    result = requests.post(**req_args)
    if result.status_code == 409:
        result = requests.put(**req_args)
    print(f"{version}: {result.status_code}")

def main():
    markdown = convert_rst_file_to_markdown("CHANGES.rst")
    for version, text in relnotes(markdown.splitlines(True)):
        update_release_note("pypi/coverage", version, text)

if __name__ == "__main__":
    main()
