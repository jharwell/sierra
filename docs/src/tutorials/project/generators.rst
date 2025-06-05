.. _tutorials/project/generators:

=======================
Generator Configuration
=======================

.. _tutorials/project/generators/scenario:

Telling SIERRA About Scenario Details
=====================================

To enable SIERRA to generate experiment definitions based on the ``--scenario``
you specify, create ``generators/scenario.py`` in your ``--project`` directory.

Within this file, you must define the following functions:

.. tabs::

   .. tab:: ``to_generator_name()``

      Takes the ``--scenario`` argument and returns the string of the callable
      function within ``scenario.py`` that SIERRA should use to generate
      scenario definitions for your experiments:

      .. code-block:: python

         def to_generator_name(scenario_arg: str) -> str:
             """
             Given ``--scenario`` string, generate the name of the callable
             generator in this file (``scenario.py``) to generate changes for
             all experiments.
             """


      .. IMPORTANT:: This is the equivalent of the ``experiment.for_all_exp()``
                     for :term:`Engines<Engine>`; :term:`Projects<Project>`
                     don't define that hook directly (at least not that SIERRA
                     uses). This alternative mechanism was used instead of
                     ``*args/**kwargs`` to share ``for_all_exp()`` signatures
                     between projects and engines, because it results in
                     better static analysis support, and is semantically just as
                     clear.



   .. tab:: ``to_dict()``

      .. code-block:: python

         def to_dict(self, scenario_name: str) -> str:
                 """
                 Given a string (presumably a result of an earlier cmdline
                 parse), parse it into a dictionary of components: arena_x,
                 arena_y, arena_z, scenario_tag

                 which specify the X,Y,Z dimensions of the arena a unique
                 tag/short scenario name unique among all scenarios for the
                 project, which is used which creating the SIERRA runtime
                 directory structure. If you aren't interested in setting the
                 dimensions of the arena from the cmdline, return -1 for the
                 X,Y,Z components.
                 """
                 ...

.. _tutorials/project/generators/exp:

Generating Experiments
======================

In ``generators/experiment.py``, you may define the following functions:

.. tabs::


   .. tab:: ``for_single_exp_run()``

      This function is optional. It is used to generate expdef changes for a
      single :term:`Experimental Run` for your project. If you define it, you
      *must* call the engine ``for_single_exp_run()`` otherwise none of the
      engine-specific changes will be made, and your experiment might not run.

      .. code-block:: python

         import pathlib

         from sierra.core.experiment import definition
         from sierra.core import types

         def for_single_exp_run(
           exp_def: definition.BaseExpDef,
           run_num: int,
           run_output_path: pathlib.Path,
           launch_stem_path: pathlib.Path,
           random_seed: int,
           cmdopts: types.Cmdopts) -> definition.BaseExpDef:
           """
           Generate expdef changes unique to a experimental run within an
           experiment for the current project.

           Return the updated experiment definition.

           Arguments:
               exp_def: The experiment definition after ``--engine`` changes
                        common to all experiments have been made.

               run_num: The run # in the experiment.

               run_output_path: Path to run output directory within experiment
                                root (i.e., a leaf).

               launch_stem_path: Path to launch file in the input directory for
                                 the experimental run, sans extension or other
                                 modifications that the engine can impose.

               random_seed: The random seed for the run.

               cmdopts: Dictionary containing parsed cmdline options.
           """
           pass
