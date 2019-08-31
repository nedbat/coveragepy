import io
import os
import re

from coverage import env
from coverage.backward import configparser, path_types, string_class, toml
from coverage.misc import CoverageException, substitute_variables


class TomlDecodeError(Exception):
    """An exception class that exists even when toml isn't installed."""


class TomlConfigParser:
    def __init__(self, our_file):
        self.getters = [lambda obj: obj['tool']['coverage']]
        if our_file:
            self.getters.append(lambda obj: obj)

        self._data = []

    def read(self, filenames):
        if isinstance(filenames, path_types):
            filenames = [filenames]
        read_ok = []
        for filename in filenames:
            try:
                with io.open(filename, encoding='utf-8') as fp:
                    self._data.append(toml.load(fp))
            except IOError:
                continue
            except toml.TomlDecodeError as err:
                raise TomlDecodeError(*err.args)
            if env.PYVERSION >= (3, 6):
                filename = os.fspath(filename)
            read_ok.append(filename)
        return read_ok

    def has_option(self, section, option):
        for data in self._data:
            for getter in self.getters:
                try:
                    getter(data)[section][option]
                except KeyError:
                    continue
                return True
        return False

    def has_section(self, section):
        for data in self._data:
            for getter in self.getters:
                try:
                    getter(data)[section]
                except KeyError:
                    continue
                return section
        return False

    def options(self, section):
        for data in self._data:
            for getter in self.getters:
                try:
                    section = getter(data)[section]
                except KeyError:
                    continue
                return list(section.keys())
        raise configparser.NoSectionError(section)

    def get_section(self, section):
        d = {}
        for opt in self.options(section):
            d[opt] = self.get(section, opt)
        return d

    def get(self, section, option):
        found_section = False
        for data in self._data:
            for getter in self.getters:
                try:
                    section = getter(data)[section]
                except KeyError:
                    continue

                found_section = True
                try:
                    value = section[option]
                except KeyError:
                    continue
                if isinstance(value, string_class):
                    value = substitute_variables(value, os.environ)
                return value
        if not found_section:
            raise configparser.NoSectionError(section)
        raise configparser.NoOptionError(option, section)

    def getboolean(self, section, option):
        value = self.get(section, option)
        if not isinstance(value, bool):
            raise ValueError(
                'Option {!r} in section {!r} is not a boolean: {!r}'
                .format(option, section, value))
        return value

    def getlist(self, section, option):
        values = self.get(section, option)
        if not isinstance(values, list):
            raise ValueError(
                'Option {!r} in section {!r} is not a list: {!r}'
                .format(option, section, values))
        for i, value in enumerate(values):
            if isinstance(value, string_class):
                values[i] = substitute_variables(value, os.environ)
        return values

    def getregexlist(self, section, option):
        values = self.getlist(section, option)
        for value in values:
            value = value.strip()
            try:
                re.compile(value)
            except re.error as e:
                raise CoverageException(
                    "Invalid [%s].%s value %r: %s" % (section, option, value, e)
                )
        return values

    def getint(self, section, option):
        value = self.get(section, option)
        if not isinstance(value, int):
            raise ValueError(
                'Option {!r} in section {!r} is not an integer: {!r}'
                .format(option, section, value))
        return value

    def getfloat(self, section, option):
        value = self.get(section, option)
        if isinstance(value, int):
            value = float(value)
        if not isinstance(value, float):
            raise ValueError(
                'Option {!r} in section {!r} is not a float: {!r}'
                .format(option, section, value))
        return value
