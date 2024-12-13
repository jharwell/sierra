Within this file, you may define the following classes, which must be named
**EXACTLY** as specified, otherwise SIERRA will not detect them. If you omit
a required class, you will get an error on SIERRA startup. If you try to use
a part of SIERRA which requires an optional class you omitted, you will get a
runtime error.

.. list-table:: Platform Plugin Classes
   :widths: 25,25,50
   :header-rows: 1

   * - Class

     - Required?

     - Conforms to interface?

   * - ExpConfigurer

     - Yes

     - :class:`~sierra.core.experiment.bindings.IExpConfigurer`

   * - ExpRunShellCmdsGenerator

     - No

     - :class:`~sierra.core.experiment.bindings.IExpRunShellCmdsGenerator`

   * - ExpShellCmdsGenerator

     - No

     - :class:`~sierra.core.experiment.bindings.IExpShellCmdsGenerator`

   * - ExecEnvChecker

     - No

     - :class:`~sierra.core.experiment.bindings.IExecEnvChecker`

Within this file, you may define the following functions, which must be named
**EXACTLY** as specified, otherwise SIERRA will not detect them. If you try
to use a part of SIERRA which requires an optional function you omitted, you
will get a runtime error.

.. list-table:: Platform Plugin Functions
   :widths: 25,25,75
   :header-rows: 1

   * - Function

     - Required?

     - Purpose

   * - cmdline_postparse_configure()

     - No

     - Performs addition modification/insertion of parsed cmdline arguments, as
       well as any needed validation for this platform.

   * - cmdline_parser

     - Yes

     - Creates and returns an ``argparse.ArgumentParser`` object containing all
       cmdline arguments understood by SIERRA when invoked with the selected
       platform.

   * - population_size_from_def()

     - Yes

     - During stage 2, on some platforms (e.g., ROS) you need to be able to
       extract the # of agents that will be used for a given
       :term:`Experiment`/:term:`Experimental Run` in order to correctly
       setup the execution environment. So, given the experimental definition
       object, extract the # agents that will be used.


   * - population_size_from_pickle()

     - Yes

     - During stage 5, there is no way for SIERRA to know how many agents
       were used in a cross-platform way, because different platforms can
       write different XML tags capturing the # agents used for a specific
       experiment. So, given an unpickled experiment definition, extract the
       # agents used.


   * - agent_prefix_extract()

     - No

     - Return the alpha-numeric prefix that will be prepended to each agent's
       numeric ID to create a UUID for the agent. Not needed by all
       platforms; if not needed by your platform, return None.


   * - arena_dims_from_criteria()

     - No

     - Get a list of the arena dimensions used in each generated
       experiment. Only needed if the dimensions are not specified on the
       cmdline, which can be useful if the batch criteria involves changing
       them; e.g., evaluating behavior with different arena shapes.

   * - pre_exp_diagnostics()

     - No

     - Log any INFO-level diagnostics to stdout before a given
       :term:`Experiment` is run. Useful to echo important execution
       environment configuration to the terminal as a sanity check.

Below is a sample/skeleton ``plugin.py`` to use as a starting point.

.. code-block:: python

   import typing as tp
   import argparse

   import implements

   from sierra.core.experiment import bindings, definition
   from sierra.core.variables import batch_criteria as bc
   from sierra.core import hpc

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

   def cmdline_parser() -> argparse.Parser:
       """
       Get a cmdline parser supporting the platform. The returned parser
       should extend :class:`~sierra.core.cmdline.BaseCmdline`.

       This example extends :class:`~sierra.core.cmdline.BaseCmdline` with:

       - :class:`~hpc.cmdline.HPCCmdline` (HPC common)
       - :class:`~cmdline.PlatformCmdline` (platform specifics)

       assuming this platform can run on HPC environments.
       """
       # Initialize all stages and return the initialized
       # parser to SIERRA for use.
       parser = hpc.HPCCmdline([-1, 1, 2, 3, 4, 5]).parser
       return cmd.PlatformCmdline(parents=[parser],
                                  stages=[-1, 1, 2, 3, 4, 5]).parser


   def cmdline_postparse_configure(argparse.Namespace) -> argparse.Namespace:
       """
       Additional configuration and/or validation of the passed cmdline
       arguments pertaining to this platform. Validation should be performed
       with assert(), and the parsed argument object should be returned with any
       modifications/additions.
       """

   def population_size_from_pickle(exp_def: tp.Union[xml.AttrChangeSet,
                                                 xml.ElementAddList]) -> int:
       """
       Size can be obtained from added tags or changed attributes; platform
       specific.

       Arguments:

           exp_def: *Part* of the pickled experiment definition object.

     """

   def population_size_from_def(exp_def: definition.XMLExpDef) -> int:
       """

       Arguments:

           exp_def: The *entire* experiment definition object.

     """

   def agent_prefix_extract(main_config: types.YAMLDict,
                            cmdopts: types.Cmdopts) -> str:
       """

       Arguments:

           main_config: Parsed dictionary of main YAML configuration.

           cmdopts: Dictionary of parsed command line options.
     """

   def pre_exp_diagnostics(cmdopts: types.Cmdopts,
                           logger: logging.Logger) -> None:
       """
       Arguments:

           cmdopts: Dictionary of parsed command line options.

           logger: The logger to log to.

     """

   def arena_dims_from_criteria(criteria: bc.BatchCriteria) -> tp.List[utils.ArenaExtent]:
       """
       Arguments:

          criteria: The batch criteria built from cmdline specification
       """
