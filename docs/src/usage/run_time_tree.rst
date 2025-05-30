.. _usage/runtime-tree:

Runtime Directory Tree
======================

.. IMPORTANT:: SIERRA **NEVER** deletes directories for you.

   So, if a directory that SIERRA needs to create already exists during stage
   {1,2}, it will abort processing in order to preserve data integrity; this is
   not necessary to do for stages {3,4,5}, because those stages can be recreated
   using the results of stages {1,2}.  This behavior can be overwridden with
   ``--exp-overwrite``, in which case the use assumes full responsibility for
   ensuring the integrity of the experiment.

   Always better to check the arguments before hitting ENTER. Measure twice, cut
   once, as the saying goes.


Basic Structure
---------------

.. list-table::
   :header-rows: 1

   * - Directory

     - Meaning

     - Configurable?

   * - SIERRA root

     - The root directory that SIERRA outputs EVERYTHING to. SIERRA will *read*
       configuration/inputs from where you tell it to, but all outputs generated
       during at any pipeline stage will appear under here.

     - `--sierra-root`. See :ref:`usage/cli` for more details.

   * - Batchroot

     - ALL files (generated experiment inputs, experiment outputs, deliverables,
       etc.) are written to this directory, which will be under
       ``--sierra-root``.  Named using a combination of:

       - ``--controller``
       - ``--scenario``
       - ``--sierra-root``
       - ``--expdef-template``
       - ``--batch-criteria``

       Subsequent experiments using the same values for these cmdline
       arguments **WILL** result in the same calculated root directory for
       experimental inputs and outputs, even if other parameters change (or if
       you change the contents of the template input file). This WILL result in
       SIERRA aborting processing during stages {1,2} if this occurs, as
       described above.

     - No.

   * - Batch input root

     - All experiment input files will be generated under this root
       directory.

     - No/named ``<batch experiment root>/exp-inputs``.

   * - Batch output root

     - All experiment output files in stage 2 will accrue under this root
       directory. Each experiment will get their own subdirectory in this root
       for its outputs to accrue into.

     - No/named ``<batch experiment root>/exp-outputs``.

   * - Batch graph root

     - All generated graphs will acrrue under this root directory. Each
       experiment will get their own subdirectory in this root for their graphs
       to accrue into.

     - No/named ``<batch experiment root>/graphs``.

   * - Batch model root

     - All model outputs will accrue under this root directory. Each experiment
       will get their own subdirectory in this root for their model outputs to
       accrue into.

     - No/named ``<batch experiment root>/models``.

   * - Batch statistics root

     - All statistics generated during stage 3 will accrue under this root
       directory. Each experiment will get their own directory in this root for
       their statistics.

     - No/named ``<batch experiment root>/statistics``.

   * - Batch imagizing root

     - All images generated during stage 3 from CSV files accrue under this root
       directory. Each experiment will get their own subdirectory in this root for
       their images.

     - No/named ``<batch experiment root>/images``.

   * - Batch video root.

     - All videos rendered during stage 4 will accrue under this root
       directory. Each experiment will get their own subdirectory in this root
       for their videos.

     - No/named ``<batch experiment root>/videos``.

   * - Batch scratch root.

     - All GNU parallel outputs, ``--exec-env`` artifacts will appear under
       here. Each experiment will get their own directory in this root for their
       own scratch. This root is separate from experiment inputs to make
       checking for segfaults, tar-ing experiments, etc. easier.

     - No/named ``<batch experiment root>/scratch``.


Default Pipeline Directory Tree (Stages 1-4)
--------------------------------------------

When SIERRA runs stages 1-4, it creates a directory structure under whatever was
passed as ``--sierra-root``. For the purposes of explanation, I will use the
following partial SIERRA option set to explain the experiment tree::

  --sierra-root=$HOME/exp\
  --controller=CATEGORY.my_controller\
  --scenario=SS.12x6\
  --engine=engine.argos\
  --batch-criteria=population_size.Log8\
  --n-runs=4\
  --expdef-template=~/my-template.argos\
  --project=fordyca


This invocation will cause SIERRA to create the following directory structure as
it runs::

  $HOME/exp
  |-- fordyca
      |-- CATEGORY.my_controller
          |-- mytemplate-SS.12x6
              |-- exp-inputs
                 |-- exp0
                     commands.txt
                     my-template_run0.argos
                     my-template_run1.argos
                     my-template_run2.argos
                     my-template_run3.argos
                 |-- exp1
                     commands.txt
                     my-template_run0.argos
                     my-template_run1.argos
                     my-template_run2.argos
                     my-template_run3.argos
                 |-- exp2
                     ...
                 |-- exp3
                     ...
                 |-- statistics
                     |-- exp0
                     |-- exp1
                     |-- exp2
                     |-- exp3
                     |-- collated
                     |-- exec
                 |-- imagize
                     |-- exp0
                     |-- exp1
                     |-- exp2
                     |-- exp3
                 |-- videos
                     |-- exp0
                     |-- exp1
                     |-- exp2
                     |-- exp3
                 |-- models
                     |-- exp0
                     |-- exp1
                     |-- exp2
                     |-- exp3
                 |-- graphs
                     |-- exp0
                     |-- exp1
                     |-- exp2
                     |-- exp3
                     |-- collated


The meaning of each directory is discussed below.

- ``$HOME/exp`` - This is the root of the directory structure (``--sierra-root``),
  and is **NOT** deleted on subsequent runs.

- ``fordyca/`` - Each project gets their own directory, so you can disambiguate
  otherwise identical SIERRA invocations and don't overwrite the directories for
  a previously used project on subsequent runs.

- ``CATEGORY.my_controller/`` - Each controller gets their own directory in the
  project root, which is **NOT** deleted on subsequent runs.

- ``mytemplate-SS.12x6/`` - The directory for the :term:`Batch Experiment` is
  named from a combination of the template input file used
  (``--expdef-template``) and the scenario (``--scenario``).

- ``exp-inputs`` - Root directory for :term:`Experimental<Experiment>` inputs;
  each experiment in the batch gets their own directory in here.

  - ``exp0/`` - Within the input directory for each experiment in the batch
    (there are 4 such directories in this example), there will be an input file
    for each :term:`Experimental Run` in the experiment, as well as a
    ``commands.txt`` used by GNU parallel to run them all in parallel. The leaf
    of the ``--expdef-template``, sans extension, has the experimental run #
    appended to it (e.g. ``my-template_run0.argos`` is the input file for
    simulation 0).

      - ``commands.txt``

      - ``my-template_run0.argos``

      - ``my-template_run1.argos``

      - ``my-template_run2.argos``

      - ``my-template_run3.argos``

  - ``exp1/``

    - ``my-template_run0.argos``

    - ``my-template_run1.argos``

    - ``my-template_run2.argos``

    - ``my-template_run3.argos``

  - ``exp2/``

    - ``...``

- ``exp-outputs/`` - Root directory for experimental outputs; each experiment
  gets their own directory in here (just like for experiment inputs). Directory
  name is controlled by the main YAML configuration.

  - ``exp0/`` - Within the output directory for each experiment in the batch
    (there are 3 such directories in this example), there will be a `directory`
    (rather than a file, as was the case for inputs) for each experimental run's
    output, including metrics, grabbed frames, etc., as configured in the expdef
    input file.

    - ``my-template_run0_output``

    - ``my-template_run1_output``

    - ``my-template_run2_output``

    - ``my-template_run3_output``

  - ``exp1/``

    - ``my-template_run0_output``

    - ``my-template_run1_output``

    - ``my-template_run2_output``

    - ``my-template_run3_output``

  - ``exp2/``

    - ``...``


- ``statistics/`` - Root directory for holding statistics calculated during
  stage3 for use during stage4.

  - ``exp0/`` - Contains the results of statistics generation for exp0
    (mean, stddev, etc., as configured).

  - ``exp1/``

  - ``exp2/``

  - ``...``

  - ``collated/`` - Contains :term:`Collated Run Output Data`
    files. During stage4, SIERRA will draw specific columns from .csv files
    under ``statistics`` according to configuration, and collate them under here
    for graph generation of *inter*\-experiment graphs.

  - ``exec/`` - Statistics about SIERRA runtime. Useful for capturing runtime of
    specific experiments to better plan/schedule time on HPC clusters.

- ``imagize/`` - Root directory for holding imagized files (averaged run outputs
  which have been converted to graphs) which can be patched together in stage 4
  to generated videos. Each experiment will get its own directory under here,
  with unique sub-directories for each different type of :term:`Experimental
  Run` data captured for imagizing. See :ref:`usage/rendering/project` for more
  details.

- ``videos/`` - Root directory for holding rendered videos generated during
  stage 4 from either captured simulator frames for imagized project files. Each
  experiment will get its own directory under here, with See
  :ref:`usage/rendering` for more details.

- ``models/`` - During stage4, the dataframes generated by all executed models
  are stored under this directory. Each experiment in the batch gets their own
  directory for `intra`\-experiment models.

- ``graphs/`` - During stage4, all generated graphs are output under this
  directory. Each experiment in the batch gets their own directory for
  `intra`\-experiment graphs.

  - ``exp0/``

  - ``exp1/``

  - ``exp2/``

  - ``exp3/``

  - ``collated/`` - Graphs which are generated across experiments in the batch
    from collated .csv data, rather than from the averaged results within each
    experiment, are output here.

Stage 5 Directory Tree
----------------------

When SIERRA runs stage 5, stages 1-4 must have already been successfully run,
and therefore the directory tree shown above will exist. For the purposes of
explanation, I will use the following partial SIERRA option sets to explain the
additions to the experiment tree for stage 5.

First, the experiment tree for `scenario comparison`::

   --pipeline 5 \
   --scenario-comparison \
   --batch-criteria population_size.Log8 \
   --scenarios-list=RN.16x16x2,PL.16x16x2 \
   --sierra-root=$HOME/exp"


This invocation will cause SIERRA to create the following directory structure as
it runs::

  $HOME/exp/
  |-- RN.16x16x2+PL.16x16x2-sc-graphs/


``RN.16x16x2+PL.16x16x2-sc-graphs/`` is the directory holding the comparison
graphs for all controllers which were previously run on the scenarios
``RN.16x16x2`` and ``PL.16x16x2`` (scenario names are arbitrary for the purposes
of stage 5 and entirely depend on the project). Inside this directory will be
all graphs generated according to the configuration specified in
:ref:`tutorials/project/stage5-config`.

Second, the experiment tree for `controller comparison` ::

  --pipeline 5 \
  --controller-comparison \
  --batch-criteria population_size.Log8 \
  --controllers-list d0.CRW,d0.DPO \
  --sierra-root=$HOME/exp"


This invocation will cause SIERRA to create the following directory structure as
it runs::


  $HOME/exp
  |-- d0.CRW+d0.DPO-cc-graphs/

``d0.CRW+d0.DPO-cc-graphs/`` is the directory holding the comparison graphs for
each scenario for which ``d0.CRW`` and ``d0.DPO`` were run (scenarios are
computed by examining the directory tree for stages 1-4). Controller names are
arbitrary for the purposes of stage 5 and entirely depend on the
project). Inside this directory will be all graphs generated according to the
configuration specified in :ref:`tutorials/project/stage5-config`.
