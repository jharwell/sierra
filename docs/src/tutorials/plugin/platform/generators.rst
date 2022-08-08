Within this file you must define the ``PlatformExpDefGenerator`` and
``PlatformExpRunDefGenerator`` classes to generate XML changes common to all
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
                     run_output_path: pathlib.Path,
                     launch_stem_path: pathlib.Path,
                     random_seed: int,
                     cmdopts: types.Cmdopts) -> None:
            pass
