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


class TextSizeConfig(tp.TypedDict):
    """Font sizes for the various text elements of a generated graph."""

    title: int
    xyz_label: int
    tick_label: int
    legend_label: int


class GraphsConfig(tp.TypedDict):
    """Typed schema for the hard-coded ``GRAPHS`` graph-rendering config."""

    static_type: str
    interactive_type: str
    dpi: int
    base_size: float
    text_size_small: TextSizeConfig
    text_size_large: TextSizeConfig

YAMLScalar = tp.Union[None, bool, str, float, int]
YAMLDict = dict[str, tp.Union[YAMLScalar, "YAMLDict", list["YAMLDict"]]]
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


@dataclass
class MainRunConfig:
    """Typed view of the ``sierra.run`` section of ``main.yaml``."""

    output_leaf: str

    @staticmethod
    def from_yaml(section: YAMLDict) -> "MainRunConfig":
        return MainRunConfig(output_leaf=str(section["output_leaf"]))


@dataclass
class MainSierraConfig:
    """Typed view of the ``sierra`` section of ``main.yaml``."""

    run: MainRunConfig

    @staticmethod
    def from_yaml(section: YAMLDict) -> "MainSierraConfig":
        run = section["run"]
        assert isinstance(run, dict), "'sierra.run' must be a mapping"
        return MainSierraConfig(run=MainRunConfig.from_yaml(run))


@dataclass
class RobotConfig:
    """Typed view of a single robot entry under ``ros.robots`` in ``main.yaml``."""

    prefix: str

    @staticmethod
    def from_yaml(entry: YAMLDict) -> "RobotConfig":
        return RobotConfig(prefix=str(entry["prefix"]))


@dataclass
class MainROSConfig:
    """Typed view of the ``ros`` section of ``main.yaml``."""

    robots: dict[str, RobotConfig]

    @staticmethod
    def from_yaml(section: YAMLDict) -> "MainROSConfig":
        robots = section["robots"]
        assert isinstance(robots, dict), "'ros.robots' must be a mapping"
        parsed: dict[str, RobotConfig] = {}
        for name, entry in robots.items():
            assert isinstance(entry, dict), f"'ros.robots.{name}' must be a mapping"
            parsed[name] = RobotConfig.from_yaml(entry)
        return MainROSConfig(robots=parsed)


@dataclass
class MainConfig:
    """Typed view over the parsed ``main.yaml`` config.

    Constructed on demand from a raw :data:`YAMLDict` at the point of use via
    :meth:`from_yaml`. This provides checked, non-``object`` attribute access to
    the config sub-schemas that SIERRA reads, without requiring the raw config
    to be threaded around as anything other than a :data:`YAMLDict`.
    """

    sierra: MainSierraConfig

    @staticmethod
    def from_yaml(config: YAMLDict) -> "MainConfig":
        sierra = config["sierra"]
        assert isinstance(sierra, dict), "'sierra' section must be a mapping"
        return MainConfig(sierra=MainSierraConfig.from_yaml(sierra))


__all__ = [
    "JSON",
    "CLIArgSpec",
    "Cmdopts",
    "GraphsConfig",
    "IntDict",
    "MainConfig",
    "MainROSConfig",
    "MainRunConfig",
    "MainSierraConfig",
    "OSPackagesSpec",
    "ParsedNodefileSpec",
    "PathList",
    "RobotConfig",
    "ShellCmdSpec",
    "SimpleDict",
    "StatisticsSpec",
    "StrDict",
    "TextSizeConfig",
    "YAMLConfigFileSpec",
    "YAMLDict",
]
