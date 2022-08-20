.. _ln-sierra-usage-pipeline:

SIERRA Pipeline
===============

When invoked SIERRA will run one or more stages of its execution path, as
specified via ``--pipeline`` on the cmdline. Only the first 4 pipeline stages
will run by default. The pipeline stages are:


Stage 1: Experiment Generation
------------------------------

Experiments using the scientific method have an independent variable whose
impact on results are measured through a series of trials. SIERRA allows you to
express this as a research query on the command line, and then parses your query
to make changes to a template input file to generate launch commands and
experimental inputs to operationalize it. Switching from targeting platform A
(e.g., ARGoS) to platform B (e.g., ROS1+Gazebo) is as easy as changing a single
command line argument. SIERRA handles the "backend" aspects of defining
experimental inputs allowing you to focus on their *content*, rather than the
mechanics of how to turn the content into something that can be executed. See
also:

- :ref:`ln-sierra-support-matrix`

- :ref:`ln-sierra-usage-cli`

Part of default pipeline.

Stage 2: Experiment Execution
-----------------------------

SIERRA runs a previously generated :term:`Batch Experiment`. Exactly which batch
experiment SIERRA runs is determined by:

- ``--controller``
- ``--scenario``
- ``--sierra-root``
- ``--template-input-file``
- ``--batch-criteria``

SIERRA currently supports two types of execution environments: simulators and
real robots, which are handled seamlessly. For simulators, SIERRA will run
multiple experimental runs from each experiment in parallel if possible. Similar
to stage 1, switching between execution environments is as easy as changing a
single command line argument. See also:

- :ref:`ln-sierra-exec-env-plugins`

- :ref:`ln-sierra-platform-plugins`

- :ref:`ln-sierra-support-matrix`

Part of default pipeline.

Stage 3: Experiment Post-Processing
-----------------------------------

SIERRA supports a number of data formats which simulations/real robot
experiments can output their data, e.g., the number of robots engaged in a given
task over time for processing.  SIERRA post-processes experimental results after
running the batch experiment; some parts of this can be done in parallel. This
includes one or more of:

- Computing statistics over/about experimental data for stage 4 for use in graph
  generation in stage 4. See :ref:`ln-sierra-usage-cli` documentation for
  ``--dist-stats`` for details.

- Creating images from project CSV files for rendering in stage 4. See
  :ref:`ln-sierra-usage-rendering-project` for details.

Part of default pipeline.

Stage 4: Deliverable Generation
-------------------------------

SIERRA can generate many deliverables from the processed experimental results
automatically (independent of the platform/execution environment!), thus greatly
simplifying reproduction of previous results if you need to tweak a given graph
(for example). SIERRA currently supports generating the following deliverables:

- Camera-ready linegraphs, heatmaps, 3D surfaces, and scatterplots directly from
  averaged/statistically processed experimental data using matplotlib.

- Videos built from frames captured during simulation or real robot operation.

- Videos built from captured experimental output .csv files.

SIERRA also has a rich model framework allowing you to run arbitrary models,
generate data, and plot it on the same figure as empirical results,
automatically. See :ref:`ln-sierra-tutorials-project-models` for details.

For some examples, see the "Generating Deliverables" section of
:xref:`2022-aamas-demo`. See :ref:`ln-sierra-usage-rendering` for details about
rendering capabilities.

Part of default pipeline.

Stage 5: Graph Generation for Controller/Scenario Comparison
------------------------------------------------------------

SIERRA can perform additional graph generation *AFTER* graph generation for
batch experiments has been run. This is extremely useful for generating graphs
which can be dropped immediately into academic papers without modification. This
can be used to compare:

- Different agent control algorithms which have all been run in the same
  ``--scenario``. See :ref:`ln-sierra-usage-stage5-intra-scenario` for details.

- A single ``--controller`` across multiple scenarios. See
  :ref:`ln-sierra-usage-stage5-inter-scenario` for details.

Not part of default pipeline.
