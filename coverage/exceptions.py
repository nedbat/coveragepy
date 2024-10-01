# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Exceptions coverage.py can raise."""

from __future__ import annotations

import os.path


def _message_append_combine_hint(message: str, is_combining: bool) -> str:
    """Append information about the combine command to error messages."""
    if not is_combining:
        message += " Perhaps 'coverage combine' must be run first."
    return message


class _BaseCoverageException(Exception):
    """The base-base of all Coverage exceptions."""
    pass


class CoverageException(_BaseCoverageException):
    """The base class of all exceptions raised by Coverage.py."""
    pass


class ConfigError(_BaseCoverageException):
    """A problem with a config file, or a value in one."""
    pass


class DataError(CoverageException):
    """An error in using a data file."""
    pass


class NoDataError(CoverageException):
    """We didn't have data to work with."""
    pass


class DataFileOrDirectoryNotFoundError(NoDataError):
    """A data file or data directory could be found."""
    @classmethod
    def new(
        cls, data_file_or_directory_path: str, *, is_combining: bool = False
    ) -> DataFileOrDirectoryNotFoundError:
        """
        Create a new instance.
        """
        message = (
            f"The data file or directory '{os.path.abspath(data_file_or_directory_path)}' could not"
            + " be found."
        )
        return cls(_message_append_combine_hint(message, is_combining))


class NoDataFilesFoundError(NoDataError):
    """No data files could be found in a data directory."""
    @classmethod
    def new(
        cls, data_directory_path: str, *, is_combining: bool = False
    ) -> 'NoDataFilesFoundError':
        """
        Create a new instance.
        """
        message = (
            f"The data directory '{os.path.abspath(data_directory_path)}' does not contain any data"
            + " files."
        )
        return cls(_message_append_combine_hint(message, is_combining))


class UnusableDataFilesError(NoDataError):
    """The given data files are unusable."""
    @classmethod
    def new(cls, *data_file_paths: str) -> 'UnusableDataFilesError':
        """
        Create a new instance.
        """
        message = (
            "The following data files are unusable, perhaps because they do not contain valid"
            + " coverage information:"
        )
        for data_file_path in data_file_paths:
            message += f"\n- '{os.path.abspath(data_file_path)}'"

        return cls(message)


class NoSource(CoverageException):
    """We couldn't find the source for a module."""
    pass


class NoCode(NoSource):
    """We couldn't find any code at all."""
    pass


class NotPython(CoverageException):
    """A source file turned out not to be parsable Python."""
    pass


class PluginError(CoverageException):
    """A plugin misbehaved."""
    pass


class _ExceptionDuringRun(CoverageException):
    """An exception happened while running customer code.

    Construct it with three arguments, the values from `sys.exc_info`.

    """
    pass


class CoverageWarning(Warning):
    """A warning from Coverage.py."""
    pass
