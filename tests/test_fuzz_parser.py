# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0

"""Fuzz test PythonParser.parse_source

This runs on OSS-Fuzz where coveragepy's set is located at:
https://github.com/google/oss-fuzz/tree/master/projects/coveragepy

It is configured to be a unit test as well, which makes it easier to test
during development, e.g. to catch breaking changes.

The goal of the fuzzing by way of OSS-Fuzz is to:
- Find any uncaught illegitimate exceptions.
- Find any security vulnerabilities as identified by pysecsan:
  https://pypi.org/project/pysecsan/
  Notice, pysecsan will be enabled by OSS-Fuzz and is not explicitly enabled
  here.
"""

import sys
import atheris
import pytest

from coverage.exceptions import NotPython
from coverage.parser import PythonParser


@pytest.mark.parametrize(
    "data",
    [
        b"random_data",
        b"more random data"
    ]
)
def TestOneInput(data):
    """Fuzzer for PythonParser."""
    fdp = atheris.FuzzedDataProvider(data)
    
    t = fdp.ConsumeUnicodeNoSurrogates(1024)
    if not t:
        return
    
    try:
        p = PythonParser(text = t)
        p.parse_source()
    except (NotPython, MemoryError) as e2:
        # Catch Memory error to avoid reporting stack overflows.
        # Catch NotPython issues as these do not signal a bug.
        pass
    except ValueError as e:
        if "source code string cannot contain null bytes" in str(e):
            # Not interesting
            pass
        else:
            raise e


def main():
    """Launch fuzzing campaign."""
    atheris.instrument_all()
    atheris.Setup(sys.argv, TestOneInput, enable_python_coverage=True)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
