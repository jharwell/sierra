.. _tutorials/cmdline:

============================
Extending the SIERRA Cmdline
============================

This tutorial covers how to extend the SIERRA cmdline for

- A new :term:`Project`

- A new :term:`Platform`

The requirements for each are largely the same, with following differences:

- All :term:`Projects<Project>`  must define the ``--scenario`` and
  ``--controller`` cmdline arguments to interact with the SIERRA core.

- The  ``Cmdline.validate()`` is only for project-based cmdlines, because of how
  SIERRA sets up the cmdline plugin; it will never be called for platform-based
  cmdlines if defined. This is generally not an issue because each project is
  associated with exactly one platform, and so can do any checks needed for the
  platform there. If you need/want to validate arguments from platforms, you can
  do that via ``cmdline_postparse_configure()`` -- see
  :ref:`tutorials/plugin/platform` for details.

- All :term:`Platforms<Platform>` must define ``--exp-setup`` and insert it into
  and the ``cmdopts`` dict via the the ``cmdopts_update()`` function.

With that out of the way, the steps to extend the SIERRA cmdline are as follows:

#. Create ``cmdline.py`` in your project/platform plugin directory.

#. Create a ``Cmdline`` class which inherits from the SIERRA cmdline as
   follows:

   .. code-block:: python

      import typing as tp
      import argparse

      import sierra.core.cmdline as cmd

      class Cmdline(cmd.CoreCmdline):
          def __init__(self,
                       bootstrap: tp.Optional[argparse.ArgumentParser],
                       stages: tp.List[int],
                       for_sphinx: bool):
              super().__init__(bootstrap, stages)

          def init_multistage(self):
              super().init_multistage(for_sphinx)

              self.multistage.add_argument("--scenario",
                                     help="""

                                     A cool scenario argument.

                                     """ + self.stage_usage_doc([1, 2, 3, 4]))

              self.multistage.add_argument("--controller",
                                     help="""

                                     A cool controller argument.

                                     """ + self.stage_usage_doc([1, 2, 3, 4]))

          def init_stage1(self):
              super().init_stage1(for_sphinx)

              self.stage1.add_argument("--my-stage1-argument",
                                       help="""

                                       An argument which is intended for stage 1 use only.

                                       """ + self.stage_usage_doc([1]),
                                       type=int,
                                       default=None)

          def init_stage2(self):
              ...
          def init_stage3(self):
              ...
          def init_stage4(self):
              ...
          def init_stage5(self):
              ...

          @staticmethod
          def cmdopts_update(cli_args: argparse.Namespace, cmdopts: types.Cmdopts):
              updates = {
              'scenario': cli_args.scenario,
              'controller': cli_args.controller,
              'my_stage1_argument': cli_args.my_stage1_argument

        }
        cmdopts.update(updates)

        def validate(self, args: argparse.Namespace) -> None:
            ...

   All of the ``init_XXstage()`` functions are optional; if they are not given
   then SIERRA will use the version in
   :class:`~sierra.core.cmdline.CoreCmdline`.

   .. IMPORTANT:: Whichever ``init_XXstage()`` functions you define must have a
                  call to ``super().init__XXstage()`` as the first statement,
                  otherwise the cmdline arguments defined by SIERRA will not be
                  setup properly.

   The ``cmdopts_update()`` function inserts the parsed cmdline arguments into
   the main ``cmdopts`` dictionary used throughout SIERRA. Keys can have any
   name, though in general it is best to make them the same as the name of the
   argument (principle of least surprise).

   The ``validate()`` function is optional, and should assert() as needed to
   check cmdline arg validity. For most cases, you shouldn't need to define this
   function; it is provided if you need to do some tricky validation beyond what
   is baked into argparse.

#. Hook your created cmdline into SIERRA.

   If you created a cmdline for a :term:`Project`, there is nothing to do!
   SIERRA will pick it up automatically.

   If you created a cmdline for a :term:`Platform`, then you will need to make
   sure your cmdline is used in the ``cmdline_parser()`` function in the
   ``plugin.py`` for your new platform (see :ref:`tutorials/plugin/platform` for
   details).
