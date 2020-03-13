SIERRA Directory Structures
===========================

SIERRA Source Code
------------------

It is helpful to know how sierra is layed out, so it is easier to see how things
fit together, and where to look for implementation details if (really `when`)
SIERRA crashes. So here is the directory structure, as seen from the root of the
repository.

- ``generators/`` - Controller and scenario generators used to modify template
  .argos files to provide the setting/context for running experiments with
  variables.

- ``graphs/`` - Generic code to generate graphs of different types.

- ``perf_measures/`` - Measures to compare performance of different controllers
  across experiments.

- ``pipeline/`` - Core pipline code in 5 stages:

  #. Generate inputs
  #. Run experiments
  #. Process results of running experiments (averaging, etc.)
  #. Generate graphs within a single experiment and between
     experiments in a batch.
  #. Generate graphs comparing batched experiments (not part of
     default pipeline).

- ``scripts/`` - Contains some ``.pbs`` scripts that can be run on MSI. Scripts
  become outdated quickly as the code base for this project and its upstream
  projects changes, so scripts should not be relied upon to work as is. Rather,
  they should be used to gain insight into how to use sierra and how to craft
  your own script.

- ``templates/`` - Contains template .argos files. Really only necessary to be
  able to change configuration that is not directly controllable via generators,
  and the # of templates should be kept small, as they need to be manually kept
  in sync with the capabilities of fordyca.

- ``variables/`` - Generators for experimental variables to modify template
  .argos files in order to run experiments with a given controller.

- ``docs/`` - Contains sphinx scaffolding/source code to generate these shiny
  docs.

- ``config/`` - Contains runtime configuration YAML files, used to fine tune how
  SIERRA functions: what graphs to generate, what controllers are valid, what
  graphs to generate for each controller, etc.

.. _ln-runtime-exp-tree:

Experiment Tree
---------------

.. important:: SIERRA **NEVER** deletes directories for you.

   Subsequent experiments using the same ``--controller``, ``--scenario``,
   ``--sierra-root``, ``--template-input-file`` **WILL** overwrite the results
   of previous experiments, even if other parameters change (or if you change
   the contents of the template input file). That bears repeating:

   `If you change other parameters but keep the same SIERRA root, controller,
   scenario, and template input file` **YOUR RESULTS WILL BE OVERWRITTEN**.

   This may or may not be desirable, so no warnings are emitted when overwriting
   happens or when it does not. While there are pitfalls with this approach, it
   is still much better than the alternative, which is to delete previous parts
   of the experiment tree if they are found to be identical to what is generated
   for the current invocation.

   Always better to check the arguments before hitting ENTER. Measure twice, cut
   once, as the saying goes.

.. warning:: Changing the ``--batch-criteria`` does not (currently) change where
   the simulation results are stored/how subtrees under ``--sierra-root`` are
   named, which `can` result in lost data, depending. This is somewhat
   counter-intuitive, hence its appearance as a standalone warning.

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

      - ``mytemplate-SS.12x6`` - The directory for the batched experiment is named
        from a combination of the template input file used
        (``--template-input-file``) and the scenario (``--scenario``).

        - ``exp-inputs`` - Root directory for experimental inputs; each experiment
          gets their own directory in here. Directory name is hardcoded (for now).

          - ``exp0`` - Within the input directory for each experiment in the batch
            (there are 4 such directories in this example), there will be an input
            file for each simulation in the experiment, as well as a
            ``commands.txt`` used by GNU parallel to run them all in parallel. The
            leaf of the ``--template-input-file``, sans extension, has the
            simulation # appended to it (e.g. ``my-template_0`` is the input file
            for simulation 0).

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

          - ``exp3``

            - ``...``

        - ``exp-outputs`` - Root directory for experimental outputs; each
          experiment gets their own directory in here (just like for experiment
          inputs). Directory name is hardcoded (for now).

          - ``exp0`` - Within the output directory for each experiment in the
            batch (there are 4 such directories in this example), there will be a
            `directory` (rather than a file, as was the case for inputs) for each
            simulation's output, including metrics, grabbed, frames, etc., as
            configured in the XML input file.

            - ``my-template_0``
            - ``my-template_1``
            - ``my-template_2``
            - ``my-template_3``
            - ``averaged-output`` - During stage3, the results for all simulations
              in the experiment are averaged together and placed into this
              directory. Directory name is controlled by the main YAML
              configuration.

          - ``exp1``

            - ``my-template_0``
            - ``my-template_1``
            - ``my-template_2``
            - ``my-template_3``
            - ``averaged-output``

          - ``exp2``

            - ``...``

          - ``exp3``

            - ``...``

          - ``collated-csvs`` - During stage4, for graphs which are generated
            across experiments in the batch (as opposed to within a single
            experiment), SIERRA will draw specific columns from .csv files under
            ``averaged-output`` (one from the averaged .csv computed for), and
            collate them under here for graph generation of `inter`\-experiment
            graphs.

        - ``graphs`` - During stage4, all generated graphs are output under this
          directory. Each experiment in the batch gets their own directory for
          `intra`\-experiment graphs.

          - ``exp0``
          - ``exp1``
          - ``exp2``
          - ``exp3``
          - ``collated-graphs`` - Graphs which are generated across experiments in
            the batch from collated .csv data, rather than from the averaged
            results within each experiment, are output here. Directory name is
            controlled by the main YAML configuration.
