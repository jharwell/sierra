# Copyright 2021 John Harwell, All rights reserved.
#
#  This file is part of SIERRA.
#
#  SIERRA is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License as published by the Free Software
#  Foundation, either version 3 of the License, or (at your option) any later
#  version.
#
#  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
#  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
#  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with
#  SIERRA.  If not, see <http://www.gnu.org/licenses/
"""Custom types defined by SIERRA for more readable type hints.

"""
# Core packages
import typing as tp
from types import ModuleType
import pathlib

# 3rd party packages

# Project packages

################################################################################
# Type Definitions
################################################################################

Cmdopts = tp.Dict[str, tp.Any]
YAMLDict = tp.Dict[str, tp.Any]
SimpleDict = tp.Dict[str, tp.Union[str, int]]

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
