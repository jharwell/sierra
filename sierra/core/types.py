# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Custom types defined by SIERRA for more readable type hints."""
# Core packages
import typing as tp
import sys
from types import ModuleType  # noqa: F401 pylint: disable=unused-import
from dataclasses import dataclass

# 2024-12-03 [JRH]: Once SIERRA moves to 3.10+ this (and many other instances)
# can be replaced unilaterally with tp.TypeAlias.
if sys.version_info < (3, 10):
    from typing_extensions import TypeAlias
else:
    from typing import TypeAlias

# 3rd party packages
import pathlib

# Project packages

################################################################################
# Type Definitions
################################################################################

Cmdopts: TypeAlias = tp.Dict[str, tp.Any]
YAMLDict: TypeAlias = tp.Union[None, bool, str, float, int, tp.Dict[str, "YAMLDict"]]
SimpleDict: TypeAlias = tp.Dict[str, tp.Union[str, int]]

# 2024-12-03 [JRH]: Once SIERRA moves to 3.10+ this (and many other instances)
# can be replaced with the '|' syntax, which is much nicer. Also the TypeAlias
# import from extensions won't be needed/will be part of the tying module.
JSON: TypeAlias = tp.Union[dict[str, "JSON"], list["JSON"], str, int, float, bool, None]

StrDict: TypeAlias = tp.Dict[str, str]
IntDict: TypeAlias = tp.Dict[str, int]
CLIArgSpec: TypeAlias = tp.Dict[str, tp.Any]
PathList: TypeAlias = tp.List[pathlib.Path]


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
    main: str
    graphs: str
    controllers: str
    models: str
    stage5: str


@dataclass
class ParsedNodefileSpec:
    hostname: str
    n_cores: int
    login: str
    port: int


@dataclass
class OSPackagesSpec:
    kernel: str
    name: str
    pkgs: tp.Dict[str, bool]


@dataclass
class StatisticsSpec:
    exts: StrDict


__all__ = [
    "ShellCmdSpec",
    "YAMLConfigFileSpec",
    "ParsedNodefileSpec",
    "OSPackagesSpec",
    "StatisticsSpec",
    "Cmdopts",
    "YAMLDict",
    "SimpleDict",
    "JSON",
    "StrDict",
    "IntDict",
    "CLIArgSpec",
    "PathList",
]
