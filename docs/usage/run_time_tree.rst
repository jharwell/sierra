.. _ln-runtime-exp-tree:

Run-Time Directory Tree
=======================

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

  --sierra-root=~/exp --controller=CATEGORY.my_controller --scenario=SS.12x6 --batch-criteria=population_size.Log8 --n-sims=4 --template-input-file=~/my-template.argos --project=fordyca


This invocation will cause SIERRA to create the following directory structure as
it runs stages 1-4:

- ``~/exp`` - This is the root of the directory structure (``--sierra-root``),
  and is **NOT** deleted on subsequent runs.

  - ``fordyca`` - Each plugin gets their own directory, so you can disambiguate
    otherwise identical SIERRA invocations and don't overwrite the directories
    for a previously used plugin on subsequent runs.

    - ``CATEGORY.my_controller`` - Each controller gets their own directory in the
      SIERRA root, which is **NOT** deleted on subsequent runs.

      - ``mytemplate-SS.12x6`` - The directory for the :term:`Batch Experiment`
        is named from a combination of the template input file used
        (``--template-input-file``) and the scenario (``--scenario``).

        - ``exp-inputs`` - Root directory for :term:`Experimental<Experiment>`
          inputs; each experiment in the batch gets their own directory in here.

          - ``exp0`` - Within the input directory for each experiment in the
            batch (there are 4 such directories in this example), there will be
            an input file for each :term:`Simulation` in the experiment, as well
            as a ``commands.txt`` used by GNU parallel to run them all in
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

          - ``exp1``

            - ``my-template_0``
            - ``my-template_1``
            - ``my-template_2``
            - ``my-template_3``

          - ``exp2``

            - ``...``


          - ``statistics`` - Root directory for holding statistics calculated
            during stage3 for use during stage4.

            - ``exp0`` - Within the directory for each experiment in the batch
              (there are 3 such directories in this example), there will be a
              `directory` for the processed experimental outputs.

          - ``exp1``

          - ``exp2``

          - ``...``

            - ``collated`` - Contains :term:`Collated .csv` files. During stage4,
              SIERRA will draw specific columns from .csv files under
              ``statistics`` according to configuration, and collate them under
              here for graph generation of `inter`\-experiment graphs.

        - ``imagize`` - Root directory for holding imagized files (averaged
          simulation outputs which have been converted to graphs) which can be
          patched together in stage 4 to generated videos. Each experiment will
          get its own directory under here, with unique sub-directories for each
          different type of simulation data captured for imagizing. See
          :ref:`ln-usage-rendering-project-imagizing` for more details.

        - ``videos`` - Root directory for holding rendered videos generated
          during stage 4 from either captured ARGoS frames for imagized project
          files. Each experiment will get its own directory under here, with
          See :ref:`ln-usage-rendering` for more details.

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
          - ``collated`` - Graphs which are generated across experiments in the
            batch from collated .csv data, rather than from the averaged results
            within each experiment, are output here.
