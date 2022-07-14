.. _ln-sierra-usage-pipeline:

SIERRA Pipeline: A Practical Summary
====================================

When invoked SIERRA will run one or more stages of its execution path, as
specified via ``--pipeline`` on the cmdline. Only the first 4 pipeline stages
will run by default. The pipeline stages are:


Stage 1: Experiment Generation
------------------------------

SIERRA generates the :term:`Batch Experiment` definition from the template
input file, :term:`Batch Criteria`, and other command line options. Part of
the default pipeline.

Stage 2: Experiment Execution
-----------------------------

SIERRA runs a previously generated :term:`Batch Experiment`. Exactly which batch
experiment SIERRA runs is determined by:

- ``--controller``
- ``--scenario``
- ``--sierra-root``
- ``--template-input-file``
- ``--batch-criteria``


SIERRA can run the experiment on any :ref:`HPC plugin <ln-sierra-exec-env-hpc>` or
:ref:`Robot plugin <ln-sierra-exec-env-robots>`.  Part of default pipeline.

Stage 3: Experiment Post-Processing
-----------------------------------

SIERRA post-processes experimental results after running the batch experiment;
some parts of this can be done in parallel. This includes one or more of:

- Computing statistics over/about experimental data for stage 4 for use in graph
  generation in stage 4. See :ref:`ln-sierra-usage-cli` documentation for
  ``--dist-stats`` for details.

- Creating images from project CSV files for rendering in stage 4. See
  :ref:`ln-sierra-usage-rendering-project` for details.

Part of default pipeline.

Stage 4: Deliverable Generation
-------------------------------

SIERRA performs deliverable generation after processing results for a batch
experiment, which can include shiny graphs and videos. See
:ref:`ln-sierra-usage-vc` for details about rendering capabilities.

Part of default pipeline.

Stage 5: Graph Generation for Controller/Scenario Comparison
------------------------------------------------------------

SIERRA can perform additional graph generation *AFTER* graph generation for
batch experiments has been run. This is extremely useful for generating graphs
which can be dropped immediately into academic papers without modification. Not
part of default pipeline. See :ref:`ln-sierra-usage-stage5` for details. This can be
used to:

- Compare multiple controllers within the same ``--scenario``. See
  :ref:`ln-sierra-usage-stage5-intra-scenario` for details.

- Compare a single ``--controller`` across multiple scenarios. See
  :ref:`ln-sierra-usage-stage5-inter-scenario` for details.
