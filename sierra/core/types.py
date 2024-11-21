# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Custom types defined by SIERRA for more readable type hints.

"""
# Core packages
import typing as tp
import sys
from types import ModuleType  # noqa: F401

# 2024-12-03 [JRH]: Once SIERRA moves to 3.10+ this (and many other instances)
# can be replaced unilaterally with tp.TypeAlias.
if sys.version_info < (3, 10):
    from typing_extensions import TypeAlias
else:
    from typing import TypeAlias

import pathlib

# 3rd party packages

# Project packages

################################################################################
# Type Definitions
################################################################################

Cmdopts = tp.Dict[str, tp.Any]
YAMLDict = tp.Dict[str, tp.Any]
SimpleDict = tp.Dict[str, tp.Union[str, int]]

# 2024-12-03 [JRH]: Once SIERRA moves to 3.10+ this (and many other instances)
# can be replaced with the '|' syntax, which is much nicer. Also the TypeAlias
# import from extensions won't be needed/will be part of the tying module.
JSON: TypeAlias = tp.Union[dict[str, "JSON"],
                           list["JSON"],
                           str,
                           int,
                           float,
                           bool,
                           None]

StrDict = tp.Dict[str, str]
IntDict = tp.Dict[str, int]
CLIArgSpec = tp.Dict[str, tp.Any]
PathList = tp.List[pathlib.Path]


class ShellCmdSpec():
    def __init__(self,
                 cmd: str,
                 shell: bool,
                 wait: bool,
                 env: tp.Optional[bool] = False) -> None:
        self.cmd = cmd
        self.shell = shell
        self.wait = wait
        self.env = env


class YAMLConfigFileSpec():
    def __init__(self,
                 main: str,
                 controllers: str,
                 models: str,
                 stage5: str) -> None:
        self.main = main
        self.controllers = controllers
        self.models = models
        self.stage5 = stage5


class ParsedNodefileSpec():
    def __init__(self,
                 hostname: str,
                 n_cores: int,
                 login: str,
                 port: int) -> None:
        self.hostname = hostname
        self.n_cores = n_cores
        self.login = login
        self.port = port


class OSPackagesSpec():
    def __init__(self,
                 kernel: str,
                 name: str,
                 pkgs: tp.Dict[str, bool]) -> None:
        self.kernel = kernel
        self.name = name
        self.pkgs = pkgs


class StatisticsSpec():
    def __init__(self,
                 exts: StrDict) -> None:
        self.exts = exts


__api__ = [
    'ShellCmdSpec',
    'YAMLConfigFileSpec',
    'ParsedNodefileSpec',
    'OSPackagesSpec'
]
