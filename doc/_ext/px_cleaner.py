"""Clean up .px files created by Sphinx."""

import sys

def clean_px(fname):
    """Clean a px file."""

    f = open(fname)
    try:
        text = f.read()
    finally:
        f.close()
    text = text.lstrip()
    f = open(fname, "w")
    try:
        f.write(text)
    finally:
        f.close()

def clean_px_files(fnames):
    for fname in fnames:
        clean_px(fname)

if __name__ == '__main__':
    clean_px_files(sys.argv[1:])

