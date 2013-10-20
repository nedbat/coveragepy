"""Clean up .px files created by Sphinx."""

import sys

def clean_px(fname):
    """Clean a px file."""

    with open(fname) as f:
        text = f.read()
    text = text.lstrip()
    with open(fname, "w") as f:
        f.write(text)

def clean_px_files(fnames):
    for fname in fnames:
        clean_px(fname)

if __name__ == '__main__':
    clean_px_files(sys.argv[1:])
