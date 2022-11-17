# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""
Parse CHANGES.md into a JSON structure.

Run with two arguments: the .md file to parse, and the JSON file to write:

	python parse_relnotes.py CHANGES.md relnotes.json

Every section that has something that looks like a version number in it will
be recorded as the release notes for that version.

"""

import json
import re
import sys


class TextChunkBuffer:
    """Hold onto text chunks until needed."""
    def __init__(self):
        self.buffer = []

    def append(self, text):
        """Add `text` to the buffer."""
        self.buffer.append(text)

    def clear(self):
        """Clear the buffer."""
        self.buffer = []

    def flush(self):
        """Produce a ("text", text) tuple if there's anything here."""
        buffered = "".join(self.buffer).strip()
        if buffered:
            yield ("text", buffered)
        self.clear()


def parse_md(lines):
    """Parse markdown lines, producing (type, text) chunks."""
    buffer = TextChunkBuffer()

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
            header = (ttype, ttext)
        elif ttype == "text":
            text.append(ttext)
        else:
            raise Exception(f"Don't know ttype {ttype!r}")
    yield (*header, "\n".join(text))


def refind(regex, text):
    """Find a regex in some text, and return the matched text, or None."""
    m = re.search(regex, text)
    if m:
        return m.group()
    else:
        return None


def fix_ref_links(text, version):
    """Find links to .rst files, and make them full RTFD links."""
    def new_link(m):
        return f"](https://coverage.readthedocs.io/en/{version}/{m[1]}.html{m[2]})"
    return re.sub(r"\]\((\w+)\.rst(#.*?)\)", new_link, text)


def relnotes(mdlines):
    r"""Yield (version, text) pairs from markdown lines.

    Each tuple is a separate version mentioned in the release notes.

    A version is any section with \d\.\d in the header text.

    """
    for _, htext, text in sections(parse_md(mdlines)):
        version = refind(r"\d+\.\d[^ ]*", htext)
        if version:
            prerelease = any(c in version for c in "abc")
            when = refind(r"\d+-\d+-\d+", htext)
            text = fix_ref_links(text, version)
            yield {
                "version": version,
                "text": text,
                "prerelease": prerelease,
                "when": when,
            }

def parse(md_filename, json_filename):
    """Main function: parse markdown and write JSON."""
    with open(md_filename) as mf:
        markdown = mf.read()
    with open(json_filename, "w") as jf:
        json.dump(list(relnotes(markdown.splitlines(True))), jf, indent=4)

if __name__ == "__main__":
    parse(*sys.argv[1:3])
