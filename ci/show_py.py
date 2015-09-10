"""Show useful things about a Python installation."""

import sys


def main():
    print("Python version:\n    {0}".format(sys.version.replace("\n", "\n    ")))
    print("Python prefix: {0}".format(sys.prefix))
    if hasattr(sys, "real_prefix"):
        print("This is a virtualenv.  The real prefix is: {0}".format(sys.real_prefix))
    else:
        print("This is not a virtualenv.")

    if sys.maxsize == 2**63-1:
        indicates = "indicating 64-bit"
    elif sys.maxsize == 2**31-1:
        indicates = "indicating 32-bit"
    else:
        indicates = "not sure what that means"
    print("sys.maxsize: {0}, {1}".format(sys.maxsize, indicates))
    if hasattr(sys, "maxint"):
        print("sys.maxint: {0}".format(sys.maxint))
    else:
        print("sys.maxint doesn't exist")

    if sys.version_info < (3, 0):
        if sys.maxunicode == 1114111:
            indicates = "indicating a wide Unicode build"
        elif sys.maxunicode == 65535:
            indicates = "indicating a narrow Unicode build"
    else:
        indicates = "as all Python 3 have"
    print("sys.maxunicode: {0}, {1}".format(sys.maxunicode, indicates))

    print("sys.getdefaultencoding(): {0}".format(sys.getdefaultencoding()))
    print("sys.getfilesystemencoding(): {0}".format(sys.getfilesystemencoding()))


if __name__ == "__main__":
    main()
