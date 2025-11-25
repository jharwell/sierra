#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#

# Core packages
import typing as tp
import argparse

# 3rd party packages

# Project packages
from sierra.core import types
from sierra.plugins import PluginCmdline


def build(parents: list[argparse.ArgumentParser], stages: list[int]) -> PluginCmdline:
    """
    Get a cmdline parser supporting the ``prod.render`` product plugin.
    """
    cmdline = PluginCmdline(parents, stages)
    cmdline.stage4.add_argument(
        "--render-cmd-opts",
        help="""
             Specify the :program:`ffmpeg` options to appear between the
             specification of the input image files and the specification of the
             output file.  The default is suitable for use with ARGoS frame
             grabbing set to a frames size of 1600x1200 to output a reasonable
             quality video.
             """
        + cmdline.stage_usage_doc([4]),
        default="-r 10 -s:v 800x600 -c:v libx264 -crf 25 -filter:v scale=-2:956 -pix_fmt yuv420p",
    )

    cmdline.stage4.add_argument(
        "--project-rendering",
        help="""
             Enable generation of videos from imagized files created as a result
             of running the ``proc.imagize`` plugin.  See
             :ref:`plugins/prod/render` for details.
             """
        + cmdline.stage_usage_doc([4]),
        action="store_true",
    )

    return cmdline


def to_cmdopts(args: argparse.Namespace) -> types.Cmdopts:
    return {
        "render_cmd_opts": args.render_cmd_opts,
        "project_rendering": args.project_rendering,
    }


def sphinx_cmdline_stage4():
    return build([], [4]).parser
