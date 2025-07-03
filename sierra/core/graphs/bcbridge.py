#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#
"""
Bridge/glue interfaces/bindings for :term:`Batch Criteria` which can be graphed.
"""

# Core packages
import pathlib
import typing as tp

# 3rd party packages
import implements

# Project packages
from sierra.core import types


class GraphInfo:
    def __init__(
        self,
        cmdopts: types.Cmdopts,
        batch_output_root: tp.Optional[pathlib.Path] = None,
        exp_names: tp.Optional[tp.List[str]] = None,
    ) -> None:
        """
        Arguments:
            cmdopts: Dictionary of parsed command line options. Most batch
                     criteria will not need this to compute things, BUT it is
                     available.

            batch_output_root: Root directory for all experimental output in the
                               batch. Needed in calculating graphs for batch
                               criteria when ``--exp-range`` is used.

            exp_names: The names of experiment directories to instantiate on the
                       filesystem.

        """
        self.cmdopts = cmdopts
        self.batch_output_root = batch_output_root
        self.exp_names = exp_names

        self.xticklabels = []  # type: tp.List[str]
        self.xticks = []  # type: tp.List[float]
        self.xlabel = ""

        self.yticklabels = []  # type: tp.List[str]
        self.yticks = []  # type: tp.List[float]
        self.ylabel = ""


class IGraphable(implements.Interface):
    """
    Interface for batch criteria which can be used with the
    :ref:`plugins/prod/graphs`.
    """

    def graph_info(
        self,
        cmdopts: types.Cmdopts,
        batch_output_root: tp.Optional[pathlib.Path] = None,
        exp_names: tp.Optional[tp.List[str]] = None,
    ) -> GraphInfo:
        """
        Generate the necessary info for generating graphs from :term:`Batch
        Criteria`.


        Arguments:
            exp_names: Needed as an optional for bivariate batch criteria.  When
                       calculating say yticks using criteria2, if criteria2 uses
                       :py:func:`populations()` in the process, the criteria's
                       OWN ``gen_exp_names()`` will be used, which will result
                       in bad directory name calculations.  This can be overcome
                       by passing the list of exp names to use at THIS level,
                       which should override the value otherwise present in
                       :class:`GraphInfo`.
        """
        raise NotImplementedError


__all__ = ["GraphInfo", "IGraphable"]
