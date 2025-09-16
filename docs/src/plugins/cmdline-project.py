import typing as tp
import argparse

from sierra.plugins import PluginCmdline

from matrix import cmdline as cmd


class Cmdline(PluginCmdline):
    """
    Defines cmdline extensions to the core command line arguments for all
    projects using the :class:`~matrix.cmdline.EngineCmdline` class.

    Arguments:

    parents: A list of other parsers which are the parents of this parser.  This
    is used to inherit cmdline options from the selected ``--execenv`` at
    runtime.  If None, then we are generating sphinx documentation from cmdline
    options.

    stages: A list of pipeline stages to add cmdline arguments for (1-5; -1 for
    multistage arguments).  During normal operation, this will be [-1, 1, 2, 3,
    4, 5].
    """

   def __init__(self,
                parents: tp.Optional[tp.List[argparse.ArgumentParser]],
                stages: tp.List[int]) -> None:
       super().__init__(parents, stages)

    def init_multistage(self) -> None:
        super().init_multistage()
        self.multistage.add_argument("--scenario",
                                     help="""

                                     A cool scenario argument.

                                     """ + self.stage_usage_doc([1, 2, 3, 4]))

        self.multistage.add_argument("--controller",
                                     help="""

                                     A cool controller argument.

                                     """ + self.stage_usage_doc([1, 2, 3, 4]))

    def validate(self, args: argparse.Namespace) -> None:
        assert args.scenario != 'scooter', "Scooter scenario not supported"



def to_cmdopts(args: argparse.Namespace) -> cmdopts: types.Cmdopts:
    return {
          'scenario': args.scenario,
          'controller': args.controller,

    }
    cmdopts.update(updates)
