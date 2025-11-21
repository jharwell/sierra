# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Custom types defined by SIERRA for more readable type hints."""
# Core packages
import typing as tp
import sys
from types import ModuleType
from dataclasses import dataclass
import pathlib

# 2024-12-03 [JRH]: Once SIERRA moves to 3.10+ this (and many other instances)
# can be replaced unilaterally with tp.TypeAlias.
if sys.version_info < (3, 10):
    from typing_extensions import TypeAlias
else:
    from typing import TypeAlias

# 3rd party packages

# Project packages

################################################################################
# Type Definitions
################################################################################

Cmdopts: TypeAlias = dict[str, tp.Any]
"""Dictionary of parsed cmdline options."""

YAMLDict: TypeAlias = tp.Union[None, bool, str, float, int, dict[str, "YAMLDict"]]
"""Parsed YAML dictionary."""

SimpleDict: TypeAlias = dict[str, tp.Union[str, int]]
"""Dictionary str -> {str|int} mappings."""

# 2024-12-03 [JRH]: Once SIERRA moves to 3.10+ this (and many other instances)
# can be replaced with the '|' syntax, which is much nicer. Also the TypeAlias
# import from extensions won't be needed/will be part of the tying module.
JSON: TypeAlias = tp.Union[dict[str, "JSON"], list["JSON"], str, int, float, bool, None]
"""Dictionary of parsed JSON."""

StrDict: TypeAlias = dict[str, str]
"""Dictionary containing str -> str mappings."""

IntDict: TypeAlias = dict[str, int]
"""Dictionary containing str -> int mappings."""

CLIArgSpec: TypeAlias = dict[str, tp.Any]
"""Dictionary containing str -> anything mappings for parsing stuff from the
cmdline into components."""

PathList: TypeAlias = list[pathlib.Path]
"""List of paths."""


@dataclass
class ShellCmdSpec:
    """
    Dataclass containing info to run shell cmds.

    Contains:

        - The cmd to run. This should end in a ';' so that multiple commands can
          be specified to run in sequence.

        - Whether or not it should be strictly run in a shell via
          ``shell=True``.

        - Whether to wait for it to finish before returning.

        - Whether to inherit the environment from the calling process.
    """

    cmd: str
    shell: bool
    wait: bool
    env: tp.Optional[bool] = False


@dataclass
class YAMLConfigFileSpec:
    """Spec for all the .yaml files available for :term:`Projects <Project>`."""

    main: str
    graphs: str
    collate: str
    controllers: str
    models: str


@dataclass
class ParsedNodefileSpec:
    """Per line in a GNU parallel style nodefil, containing info a single resource."""

    hostname: str
    n_cores: int
    login: str
    port: int


@dataclass
class OSPackagesSpec:
    """Info about what packages are required/optional on a given OS."""

    kernel: str
    name: str
    pkgs: dict[str, bool]


@dataclass
class StatisticsSpec:
    """Spec mapping file types of statistics to file extensions to contain said stats."""

    exts: StrDict


__all__ = [
    "JSON",
    "CLIArgSpec",
    "Cmdopts",
    "IntDict",
    "OSPackagesSpec",
    "ParsedNodefileSpec",
    "PathList",
    "ShellCmdSpec",
    "SimpleDict",
    "StatisticsSpec",
    "StrDict",
    "YAMLConfigFileSpec",
    "YAMLDict",
]
