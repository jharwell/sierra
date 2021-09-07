.. _ln-usage-pipeline:

SIERRA Pipeline
===============

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


SIERRA can run the experiment on any :ref:`HPC plugin <ln-hpc-plugins>`.  Part
of default pipeline.

Stage 3: Experiment Post-Processing
-----------------------------------

SIERRA post-processes experimental results after running the batched experiment;
some parts of this can be done in parallel. This includes one or more of:

- Computing statistics over/about experimental data for stage 4 for use in graph
  generation in stage 4. See :ref:`ln-usage-statistics` for details.

- Creating images from project ``.csv`` files for rendering in stage 4. See
  :ref:`ln-usage-rendering-project` for details.

Part of default pipeline.

Stage 4: Deliverable Generation
-------------------------------

SIERRA performs deliverable generation after processing results for a batched
experiment, which can include shiny graphs and videos. See
:ref:`ln-usage-rendering` for details about rendering capabilities.

Part of default pipeline.

Stage 5: Graph Genertion for Controller Comparison
--------------------------------------------------

SIERRA perform graph generation for comparing controllers AFTER graph generation
for batched experiments has been run. Not part of default pipeline.

.. IMPORTANT:: It is assumed that if stage5 is run that the # experiments and
               batch criteria are the same for all controllers that will be
               compared. If this is not true then weird things may or may not
               happen. Some level of checking and verification is performed
               prior to comparison, but this functionality is alpha quality at
               best.


.. IMPORTANT:: If you run something other than ``--pipeline 1 2 3 4``, then
  before stage X will run without crashing, you need to run stage X-1. This is a
  logical limitation, because the differente pipeline stages build on each other.
