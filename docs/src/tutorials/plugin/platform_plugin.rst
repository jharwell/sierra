.. _ln-sierra-tutorials-plugin-platform:

==============================
Creating a New Platform Plugin
==============================

For the purposes of this tutorial, I will assume you are creating a new
:term:`Platform` :term:`Plugin` ``matrix``, and the code for that plugin lives
in ``$HOME/git/plugins/platform/matrix``.

If you are creating a new platform, you have two options.

#. Create a stand-alone platform, providing your own definitions for all of the
   necessary functions/classes below.

#. Derive from an existing platform by simply calling the "parent" platform's
   functions/calling in your derived definitions except when you need to
   actually extend them (e.g., to add support for a new HPC plugin)

In either case, the steps to actually create the code are below.

Create the Code
===============

Create the following filesystem structure and content in
``$HOME/git/plugins/platform/matrix``. Each file is required; any number of
additional files can be included.


#. ``plugin.py``

   Within this file, you must define the following classes:

   .. code-block:: python

      import typing as tp
      import argparse

      import implements

      from sierra.core.experiment import bindings, xml, definition

      @implements.implements(bindings.IParsedCmdlineConfigurer)
      class CmdlineParserGenerator():
        def __call__() -> argparse.ArgumentParser:
            """A class that conforms to
            :class:`~sierra.core.experiment.bindings.ICmdlineParserGenerator`.
            """
            # As an example, assuming this platform can run on HPC
            # environments. Initialize all stages and return the initialized
            # parser to SIERRA for use.
            parser = hpc.HPCCmdline([-1, 1, 2, 3, 4, 5]).parser
            return cmd.PlatformCmdline(parents=[parser],
                                       stages=[-1, 1, 2, 3, 4, 5]).parser


      @implements.implements(bindings.IParsedCmdlineConfigurer)
      class ParsedCmdlineConfigurer():
        """A class that conforms to
        :class:`~sierra.core.experiment.bindings.IParsedCmdlineConfigurer`.
        """

      @implements.implements(bindings.IExpShellCmdsGenerator)
      class ExpShellCmdsGenerator():
        """A class that conforms to
        :class:`~sierra.core.experiment.bindings.IExpShellCmdsGenerator`.
        """

      @implements.implements(bindings.IExpRunShellCmdsGenerator)
      class ExpRunShellCmdsGenerator():
        """A class that conforms to
        :class:`~sierra.core.experiment.bindings.IExpRunShellCmdsGenerator`.
        """

      @implements.implements(bindings.IExecEnvChecker)
      class ExecEnvChecker():
        """A class that conforms to
        :class:`~sierra.core.experiment.bindings.IExecEnvChecker`.
        """

      @implements.implements(bindings.IExpConfigurer)
      class ExpConfigurer():
        """A class that conforms to
        :class:`~sierra.core.experiment.bindings.IExpConfigurer`.
        """

      @implements.implements(bindings.IExpRunConfigurer)
      class ExpRunConfigurer():
        """A class that conforms to
        :class:`~sierra.core.experiment.bindings.IExpRunConfigurer`.
        """

      def population_size_from_pickle(def: tp.Union[xml.AttrChangeSet,
                                                    xml.TagAddList]) -> int:
        """
        During stage 5, there is no way for SIERRA to know how many robots
        were used in a cross-platform way, because different platforms can
        write different XML tags capturing the # robots used for a specific
        experiment. So, given an unpickled experiment definition, extract the
        # robots used.

        """
        # As an example, assuming that for the matrix platform there is
        # always a "system/size" attribute.
        for path, attr, value in exp_def:
            if path == ".//system" and attr == "size":
                return int(value)

      def population_size_from_def(exp_def: definition.XMLExpDef) -> int:
        """
        During stage 2, on some platforms (e.g., ROS) you need to be able to
        extract the # of robots that will be used for a given
        :term:`Experiment`/:term:`Experimental Run` in order to correctly
        setup the execution environment. So, given the experimental
        definition object, extract the # robots that will be used.

        """

      def robot_prefix_extract(main_config: types.YAMLDict,
                               cmdopts: types.Cmdopts) -> tp.Optional[str]:
        """
        Return the alpha-numeric prefix that will be prepended to each robot's
        numeric ID to create a UUID for the robot. Not needed by all
        platforms; if not needed by your platform, return None.
        """

      def pre_exp_diagnostics(cmdopts: types.Cmdopts,
                              logger: logging.Logger) -> None:
        """
        Log any INFO-level diagnostics to stdout before a given
        :term:`Experiment` is run. Useful to echo important execution
        environment configuration to the terminal as a sanity check.

        """

#. ``cmdline.py``

   Within this file you must define the ``PlatformCmdline`` class as shown
   below.

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

#. ``generators/platform_generators.py``

   Within this file you must define the ``PlatformExpDefGenerator`` and
   ``PlatformExpRunDefGenerator`` to generate XML changes common to all
   experiment runs for your platform and per-run changes, respectively.

   .. code-block:: python

      from sierra.core.experiment import definition

      class PlatformExpDefGenerator():
          """
          Create an experiment definition from the
          ``--template-input-file`` and generate XML changes to input files
          that are common to all experiments on the platform. All projects
          using this platform should derive from this class for `their`
          project-specific changes for the platform.

          Arguments:
              spec: The spec for the experimental run.
              controller: The controller used for the experiment, as passed
                          via ``--controller.
          cmdopts: Dictionary of parsed cmdline parameters.
          kwargs: Additional arguments.
          """

          def __init__(self,
                       spec: ExperimentSpec,
                       controller: str,
                       cmdopts: types.Cmdopts,
                       **kwargs) -> None:
              pass

          def generate(self) -> definition.XMLExpDef:
              pass

       class PlatformExpRunDefUniqueGenerator:
           """
           Generate XML changes unique to a experimental run within an
           experiment for the matrix platform.

           Arguments:
               run_num: The run # in the experiment.

               run_output_path: Path to run output directory within
                                experiment root (i.e., a leaf).

               launch_stem_path: Path to launch file in the input directory
                                 for the experimental run, sans extension
                                 or other modifications that the platform
                                 can impose.

               random_seed: The random seed for the run.

               cmdopts: Dictionary containing parsed cmdline options.
           """
           def __init__(self,
                        run_num: int,
                        run_output_path: str,
                        launch_stem_path: str,
                        random_seed: int,
                        cmdopts: types.Cmdopts) -> None:
               pass


Connect to SIERRA
=================

#. Put ``$HOME/git/plugins/platform/matrix`` on your
   :envvar:`SIERRA_PLUGIN_PATH` so that your platform can be selected via
   ``--platform=platform.matrix``.
