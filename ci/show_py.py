"""Show useful things about a Python installation."""

import sys


def main():
    show_version()
    show_sizes()
    show_encoding()
    show_path()


def show_version():
    print("Python version:\n    {0}".format(sys.version.replace("\n", "\n    ")))
    print("Python executable: {0!r}".format(sys.executable))
    print("Python prefix: {0!r}".format(sys.prefix))
    if hasattr(sys, "real_prefix"):
        print("This is a virtualenv.  The real prefix is: {0!r}".format(sys.real_prefix))
    else:
        print("This is not a virtualenv.")


def show_sizes():
    if sys.maxsize == 2**63-1:
        indicates = "indicating 64-bit"
    elif sys.maxsize == 2**31-1:
        indicates = "indicating 32-bit"
    else:
        indicates = "not sure what that means"
    print("sys.maxsize: {0!r}, {1}".format(sys.maxsize, indicates))
    if hasattr(sys, "maxint"):
        print("sys.maxint: {0!r}".format(sys.maxint))
    else:
        print("sys.maxint doesn't exist")


def show_encoding():
    if sys.version_info < (3, 0):
        if sys.maxunicode == 1114111:
            indicates = "indicating a wide Unicode build"
        elif sys.maxunicode == 65535:
            indicates = "indicating a narrow Unicode build"
    else:
        indicates = "as all Python 3 have"
    print("sys.maxunicode: {0!r}, {1}".format(sys.maxunicode, indicates))

    print("sys.getdefaultencoding(): {0!r}".format(sys.getdefaultencoding()))
    print("sys.getfilesystemencoding(): {0!r}".format(sys.getfilesystemencoding()))


def show_path():
    print("sys.path:")
    print("\n".join("    {0!r}".format(p) for p in sys.path))


if __name__ == "__main__":
    main()
