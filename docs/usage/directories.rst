.. _ln-directory-structures:

SIERRA Directory Structures
===========================

SIERRA Source Code
------------------

It is helpful to know how SIERRA is layed out, so it is easier to see how things
fit together, and where to look for implementation details if (really `when`)
SIERRA crashes. So here is the directory structure, as seen from the root of the
repository.

- ``core/`` - The parts of SIERRA which are (mostly) agnostic to the project
  being run. This is not strictly true, as there are still many elements that
  are tied to _my_ projects, but decoupling is an ongoing process.

  - ``generators/`` - Generic controller and scenario generators used to modify
    template ``.argos`` files to provide the setting/context for running
    experiments with variables.

  - ``graphs/`` - Generic code to generate graphs of different types.

  - ``perf_measures/`` - Generic measures to compare performance of different
    controllers across experiments.

  - ``config/`` - Contains runtime configuration YAML files, used to fine tune
    how SIERRA functions: what graphs to generate, what controllers are valid,
    what graphs to generate for each controller, etc., which are common to all
    projects.

  - ``pipeline/`` - Core pipline code in 5 stages:

    #. Generate inputs
    #. Run experiments
    #. Process results of running experiments (averaging, etc.)
    #. Generate graphs within a single experiment and between
       experiments in a batch.
    #. Generate graphs comparing batched experiments (not part of
       default pipeline).

  - ``variables/`` - Genertic generators for experimental variables to modify
    template ``.argos`` files in order to run experiments with a given
    controller.

- ``scripts/`` - Contains some ``.pbs`` scripts that can be run on MSI. Scripts
  become outdated quickly as the code base for this project and its upstream
  projects changes, so scripts should not be relied upon to work as is. Rather,
  they should be used to gain insight into how to use sierra and how to craft
  your own script.

- ``templates/`` - Contains template ``.argos`` files. Really only necessary to
  be able to change configuration that is not directly controllable via
  generators, and the # of templates should be kept small.

- ``docs/`` - Contains sphinx scaffolding/source code to generate these shiny
  docs.

.. _ln-runtime-exp-tree:

Experiment Tree
---------------

.. IMPORTANT:: SIERRA **NEVER** deletes directories for you.

   Subsequent experiments using the same values for the following cmdline
   components **WILL** result in the same calculated root directory for
   experimental inputs and outputs, even if other parameters change (or if you
   change the contents of the template input file):

   - ``--controller``
   - ``--scenario``
   - ``--sierra-root``
   - ``--template-input-file``
   - ``--batch-criteria``

   SIERRA will abort stage{1,2} processing when this occurs in order to preserve
   data integrity; this behavior can be overwridden with ``--exp-overwrite``, in
   which case the use assumes full responsibility for ensuring the integrity of
   the experiment.

   Always better to check the arguments before hitting ENTER. Measure twice, cut
   once, as the saying goes.

When SIERRA runs, it creates a directory structure under whatever was passed as
``--sierra-root``. For the purposes of explanation, I will use the following
partial SIERRA option set to explain the experiment tree::

  --sierra-root=~/exp --controller=CATEGORY.my_controller --scenario=SS.12x6 --batch-criteria=population_size_.Log8 --n-sims=4 --template-input-file=~/my-template.argos --plugin=fordyca


This invocation will cause SIERRA to create the following directory structure as
it runs stages 1-4:

- ``~/exp`` - This is the root of the directory structure (``--sierra-root``),
  and is **NOT** deleted on subsequent runs.

  - ``fordyca`` - Each plugin gets their own directory, so you can disambiguate
    otherwise identical SIERRA invocations and don't overwrite the directories
    for a previously used plugin on subsequent runs.

    - ``CATEGORY.my_controller`` - Each controller gets their own directory in the
      SIERRA root, which is **NOT** deleted on subsequent runs.

      - ``mytemplate-SS.12x6`` - The directory for the batched experiment is
        named from a combination of the template input file used
        (``--template-input-file``) and the scenario (``--scenario``).

        - ``exp-inputs`` - Root directory for experimental inputs; each
          experiment gets their own directory in here. Directory name is
          controlled by the main YAML configuration.

          - ``exp0`` - Within the input directory for each experiment in the
            batch (there are 4 such directories in this example), there will be
            an input file for each simulation in the experiment, as well as a
            ``commands.txt`` used by GNU parallel to run them all in
            parallel. The leaf of the ``--template-input-file``, sans extension,
            has the simulation # appended to it (e.g. ``my-template_0`` is the
            input file for simulation 0).

              - ``commands.txt``
              - ``my-template_0``
              - ``my-template_1``
              - ``my-template_2``
              - ``my-template_3``

          - ``exp1``

            - ``my-template_0``
            - ``my-template_1``
            - ``my-template_2``
            - ``my-template_3``

          - ``exp2``

            - ``...``

        - ``exp-outputs`` - Root directory for experimental outputs; each
          experiment gets their own directory in here (just like for experiment
          inputs). Directory name is controlled by the main YAML configuration.

          - ``exp0`` - Within the output directory for each experiment in the
            batch (there are 3 such directories in this example), there will be
            a `directory` (rather than a file, as was the case for inputs) for
            each simulation's output, including metrics, grabbed, frames, etc.,
            as configured in the XML input file.

            - ``my-template_0``
            - ``my-template_1``
            - ``my-template_2``
            - ``my-template_3``
            - ``averaged-output`` - During stage3, the results for all
              simulations in the experiment are averaged together and placed
              into this directory. Directory name is controlled by the main YAML
              configuration.

          - ``exp1``

            - ``my-template_0``
            - ``my-template_1``
            - ``my-template_2``
            - ``my-template_3``
            - ``averaged-output``

          - ``exp2``

            - ``...``

          - ``collated-csvs`` - During stage4, for graphs which are generated
            across experiments in the batch (as opposed to within a single
            experiment), SIERRA will draw specific columns from .csv files under
            ``averaged-output`` according to configuration, and collate them
            under here for graph generation of `inter`\-experiment graphs.

        - ``models`` - During stage4, the dataframes generated by all executed
          models are stored under this. Each experiment in the batch gets their
          own directory for `intra`\-experiment models.

        - ``graphs`` - During stage4, all generated graphs are output under this
          directory. Each experiment in the batch gets their own directory for
          `intra`\-experiment graphs.

          - ``exp0``
          - ``exp1``
          - ``exp2``
          - ``exp3``
          - ``collated-graphs`` - Graphs which are generated across experiments
            in the batch from collated .csv data, rather than from the averaged
            results within each experiment, are output here. Directory name is
            controlled by the main YAML configuration.
