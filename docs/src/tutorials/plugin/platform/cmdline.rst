Within this file you must define the ``PlatformCmdline`` class. A sample
implementation is shown below to use as a starting bound. All member functions
are optional.

.. code-block:: python

   import typing as tp
   import argparse

   from sierra.core import types
   from sierra.core import config
   import sierra.core.cmdline as cmd
   import sierra.core.hpc as hpc

   class PlatformCmdline(cmd.BaseCmdline):
       """
       Defines cmdline extensions to the core command line arguments
       defined in :class:`~sierra.core.cmdline.CoreCmdline` for the
       ``matrix`` platform. Any projects using this platform should
       derive from this class.

       Arguments:

           parents: A list of other parsers which are the parents of
                    this parser. This is used to inherit cmdline options
                    from the selected ``--exec-env`` at runtime. If
                    None, then we are generating sphinx documentation
                    from cmdline options.

            stages: A list of pipeline stages to add cmdline arguments
                    for (1-5; -1 for multistage arguments). During
                    normal operation, this will be [-1, 1, 2, 3, 4, 5].

       """

        def __init__(self,
                     parents: tp.Optional[tp.List[argparse.ArgumentParser]],
                     stages: tp.List[int]) -> None:

            # Normal operation when running sierra-cli
            if parents is not None:
                self.parser = argparse.ArgumentParser(prog='sierra-cli',
                                                      parents=parents,
                                                      allow_abbrev=False)
            else:
                # Optional--only needed for generating sphinx documentation
                self.parser = argparse.ArgumentParser(prog='sierra-cli',
                                                      allow_abbrev=False)

            # Initialize arguments according to configuration
            self.init_cli(stages)

        def init_cli(self, stages: tp.List[int]) -> None:
            if -1 in stages:
                self.init_multistage()

            if 1 in stages:
                self.init_stage1()

            # And so on...

        def init_stage1(self) -> None:
            # Experiment options
            experiment = self.parser.add_argument_group(
                'Stage1: Red pill or blue pill')

            experiment.add_argument("--pill-type",
                                    choices=["red", "blue"],
                                    help="""Red or blue""",
                                    default="red")

        def init_multistage(self) -> None:
            neo = self.parser.add_argument_group('Neo Options')

            neo.add_argument("--using-powers",
                             help="""Do you believe you're the one or not?""",
                             action='store_true')
