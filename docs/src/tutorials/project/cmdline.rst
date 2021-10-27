.. _ln-tutorials-project-cmdline:

============================
Extending the SIERRA Cmdline
============================

At a minimum, all :term:`Projects<Project>` must define the ``--scenario`` and
``--controller`` cmdline arguments to interact with the SIERRA core; other
cmdline arguments can be added in the same manner. For example, you might want
to control aspects of experiment generation outside of those controlled by
``--scenario``, but only some of the time. To add additional cmdline options to
the SIERRA, follow the steps below.

#. Create ``cmdline.py`` in your :term:`Project` directory.

#. Create a ``Cmdline`` class which inherits from the SIERRA cmdline as
   follows:

   .. code-block:: python

      import typing as tp
      import sierra.core.cmdline as cmd

      class Cmdline(cmd.CoreCmdline):
          def __init__(self,
                       bootstrap: tp.Optional[argparse.ArgumentParser],
                       stages: tp.List[int],
                       for_sphinx: bool):
              super().__init__(bootstrap, stages)

          def init_multistage(self, for_sphinx: bool):
              super().init_multistage(for_sphinx)

              self.multistage.add_argument("--scenario",
                                     help="""

                                     A cool scenario argument.

                                     """ + self.stage_usage_doc([1, 2, 3, 4]))

              self.multistage.add_argument("--controller",
                                     help="""

                                     A cool controller argument.

                                     """ + self.stage_usage_doc([1, 2, 3, 4]))

          def init_stage1(self, for_sphinx: bool):
              super().init_stage1(for_sphinx)

              self.stage1.add_argument("--my-stage1-argument",
                                       help="""

                                       An argument which is intended for stage 1 use only.

                                       """ + self.stage_usage_doc([1]),
                                       type=int,
                                       default=None)

          def init_stage2(self, for_sphinx: bool):
              ...
          def init_stage3(self, for_sphinx: bool):
              ...
          def init_stage4(self, for_sphinx: bool):
              ...
          def init_stage5(self, for_sphinx: bool):
              ...

          @staticmethod
          def cmdopts_update(cli_args, cmdopts: tp.Dict[str, tp.Any]):
              updates = {
              'scenario': cli_args.scenario,
              'controller': cli_args.controller,
              'my_stage1_argument': cli_args.my_stage1_argument

        }
        cmdopts.update(updates)

   The ``for_sphinx`` argument to ``__init__()`` is used for generated correctly
   formatting docs for the different stages of SIERRA which include the docs
   from your cmdline arguments, and is ignored for this tutorial.

   All of the ``init_XXstage()`` functions are optional; if they are not given
   then SIERRA will use the version in ``CoreCmdline``.

   .. IMPORTANT:: Whichever ``init_XXstage()`` functions you define must have a
                  call to ``super().init__XXstage()`` as the first statement,
                  otherwise the cmdline arguments defined by SIERRA will not be
                  setup properly.

   The ``cmdopts_update()`` function inserts the parsed cmdline arguments into
   the main ``cmdopts`` dictionary used throughout SIERRA. Keys can have any
   name, though in general it is best to make them the same as the name of the
   argument (principle of least surprise).

#. Create a ``CmdlineValidator`` class to validate the additional cmdline
   arguments you pass (can be empty class if no additional validation is
   needed). Generally this should be used for things like "if X is passed then Y
   must also be passed".

   .. code-block:: python

      class CmdlineValidator(cmd.CoreCmdlineValidator):
          def __call__(self, args) -> None:
              assert args.my_stage1_argument is not None,\
                   "--my-stage1-argument must be passed!"

   The ``__call__()`` function is passed the ``argparse`` object resulting from
   parsing the arguments, which can be used as you would expect to perform
   checks. All checks should be assertions.

