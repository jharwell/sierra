Within this file may define the following functions:

.. list-table:: Platform Generator Functions
   :widths: 10 10 80
   :header-rows: 1

   * - Function

     - Required?

     - Purpose

   * - for_all_exp()

     - Yes

     - Generate expdef changes common to all :term:`Experiment Runs<Experimental
       Run>` in an :term:`Experiment` for your platform.

   * - for_single__exp_run()

     - Yes

     - Generate expdef changes for a single :term:`Experimental Run` for your
       platform.

Below is a sample/skeleton ``platform_generators.py`` to use and a starting
point.

.. code-block:: python

   import pathlib

   from sierra.core.experiment import definition
   from sierra.core import types
   from sierra.experiment import spec

   def for_all_exp(spec: spec.ExperimentSpec,
                   controller: str,
                   cmdopts: types.Cmdopts,
                   expdef_template_fpath: pathlib.Path) -> definition.BaseExpDef:
       """
       Create an experiment definition from the
       ``--expdef-template`` and generate XML changes to input files
       that are common to all experiments on the platform. All projects
       using this platform should derive from this class for `their`
       project-specific changes for the platform.

       Arguments:

           spec: The spec for the experimental run.

           controller: The controller used for the experiment, as passed
                       via ``--controller``.

           exp_def_template_fpath: The path to ``--expdef-template``.
       """
       pass

   def for_single_exp_run(
        exp_def: definition.BaseExpDef,
        run_num: int,
        run_output_path: pathlib.Path,
        launch_stem_path: pathlib.Path,
        random_seed: int,
        cmdopts: types.Cmdopts) -> definition.BaseExpDef:
        """
        Generate expdef changes unique to a experimental run within an
        experiment for the matrix platform.

        Arguments:
            exp_def: The experiment definition after ``--platform`` changes
            common to all experiments have been made.

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
        pass
