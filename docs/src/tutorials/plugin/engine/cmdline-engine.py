import typing as tp
import argparse

import sierra.core.cmdline as corecmd
from sierra.core import types


class Cmdline(corecmd.BaseCmdline):
    """
    Defines cmdline extensions to the core command line arguments
    defined in :class:`~sierra.core.cmdline.CoreCmdline` for the
    ``matrix`` engine. Any projects using this engine should
    derive their cmdlines from this class.

    Arguments:

        parents: A list of other parsers which are the parents of
                 this parser. This is used to inherit cmdline options
                 from the selected ``--execenv`` at runtime. If
                 None, then we are generating sphinx documentation
                 from cmdline options.

         stages: A list of pipeline stages to add cmdline arguments
                 for (1-5; -1 for multistage arguments). During
                 normal operation, this will be [-1, 1, 2, 3, 4, 5].

    """

    def init_stage1(self) -> None:
        super().init_stage1()

        # Experiment options
        experiment = self.parser.add_argument_group(
            'Stage1: Red pill or blue pill')

        experiment.add_argument("--pill-type",
                                choices=["red", "blue"],
                                help="""Red or blue""",
                                default="red")

    def init_multistage(self) -> None:
        super().init_multistage()

        neo = self.parser.add_argument_group('Neo Options')

        neo.add_argument("--using-powers",
                         help="""Do you believe you're the one or not?""",
                         action='store_true')


def to_cmdopts(args: argparse.Namespace) -> cmdopts: types.Cmdopts:
    return {
        'pill_type': args.pill_type,
        'using_powers': args.using_powers
    }
