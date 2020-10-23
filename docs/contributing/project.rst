How to Add A New Project
========================

The argument to the cmdline option ``--project`` is added to the path
``projects/<option>``, and the plugin directory tree must have the following
structure and content (a subset of the SIERRA core directory structure):

- ``config/`` - Plugin YAML configuration root. within this directory, the following
  files are used (not all files are required when running a stage that utilizes
  them):

  - ``main.yaml`` - Main SIERRA configuration file. This file is required for all
    pipeline stages.

  - ``controllers.yaml`` - Configuration for controllers (input file/graph
    generation). This file is required for all pipeline stages.

  - ``intra-graphs-line.yaml`` - Configuration for intra-experiment
    linegraphs. This file is optional. If it is present, graphs defined in it
    will be added to those specified in ``core/config/intra-graphs-line.yaml``,
    and will be generated if stage 4 is run.

  - ``intra-graphs-hm.yaml`` - Configuration for intra-experiment
    heatmaps. This file is optional. If it is present, graphs defined in it will
    be added to those specified in ``core/config/intra-graphs-hm.yaml``, and
    will be generated if stage 4 is run.

  - ``inter-graphs.yaml`` - Configuration for inter-experiment graphs. This file
    is optional. If it is present, graphs defined in it will be added to those
    specified in ``core/config/inter-graphs-line.yaml``, and will be generated
    if stage 4 is run.

  - ``stage5.yaml`` - Configuration for stage5 controller comparisons. This file
    is required if stage5 is run, and optional otherwise.

  - ``models.yaml`` - Configuration for intra- and inter-experiment models. This
    file is optional. If it is present, models defined and enabled in it will be
    run before stage 4 intra- and/or inter-experiment graph generation, if stage
    4 is run.

- ``generators/scenario_generators.py`` - Specifies extensions/specializations
  of the foraging scenarios in the SIERRA core, as well as any other scenarios
  the user would want to be able to pass via the ``--scenario`` cmdline
  argument.

- ``variables/`` - Additional variables (including batch criteria) defined by
  the plugin/project that can be directly or indirectly used by the
  ``--batch-criteria`` and ``--scenario`` cmdline arguments.

- ``cmdline.py`` - Specifies cmdline extensions specific to the plugin/project.

Contents of ``config/main.yaml``
--------------------------------

Root level dictionaries:

- ``sim`` - Configuration for each ARGoS simulation run. This dictionary is
  mandatory for all simulations.

- ``sierra`` - Configuration for SIERRA internals. This dictionary is mandatory
  for all simulations.

- ``perf`` - Configuration for performance measures. This dictionary is
  mandatory for all simulations.

``sim`` dictionary
##################
.. code-block:: YAML

   sim:

     # The directory within each simulation's working directory which will
     # @ contain the metrics output as by the simulation. This key is mandatory
     # for all simulations.
     sim_metrics_leaf: 'metrics'

     # The directory within each simulation's working directory which will
     # contain the frames output by ARGoS during simulation, if frame grabbing
     # is configured. This key is currently mandatory for all simulations, even
     # if rendering/frame grabbing is not employed.
     argos_frames_leaf: 'frames'

``sierra`` dictionary
#####################
.. code-block:: YAML

   sierra:

     # The leaf directory under the compute batched experiment root where
     # inter-experiment ``.csv`` files will be created as the results of
     # individual experiments within the batch are collated #together. This key
     # is mandatory for all simulations.
     collate_csv_leaf: 'collated-csvs'

     # The leaf directory under the ``graphs/`` directory within the batched
     # experiment root where inter-experiment graphs created from the
     # inter-experiment collated ``.csv`` files will be created. This key is
     mandatory for all simulations.  collate_graph_leaf: 'collated-graphs'

     # The leaf directory within the output directory for each experiment
     # within the batch where the averaged ``.csv`` files for all simulations in
     # the experiment will be placed. This key is mandatory for all simulations.
     avg_output_leaf: 'averaged-output'

     # The directory within the output directory for each experiment within
     # the batch where the frames created from the ``.csv`` files created by the
     # selected project plugin will be stored for rendering. This key is
     # currently mandatory for all simulations, even if rendering/frame grabbing
     is not employed.
     plugin_frames_leaf: 'plugin-frames'

``perf`` dictionary
###################
.. code-block:: YAML

   perf:

     # Is the performance measure for the project inverted, meaning that lower
     # values are better (as opposed to higher values, which is the default if
     # this is omitted) ?
     inverted: true

     # The title that graphs of raw swarm performance should have (cannot be
     # known a priori for all possible projects during stage 4).
     raw_perf_title: 'Swarm Blocks Collected'

     # The Y label for graphs of raw swarm performance (cannot be
     # known a priori for all possible projects during stage 4).
     raw_perf_ylabel: '# Blocks'

     # The ``.csv`` file under ``avg_output_leaf`` for each experiment which
     # contains the performance information for the experiment.
     intra_perf_csv: 'block-transport.csv'

     # The ``.csv`` column within ``intra_perf_csv`` which is the
     temporally charted performance measure for the experiment.
     intra_perf_col: 'cum_avg_transported'

     # The collated ``.csv`` containing overall performance measures for each
     # experiment in the batch (1 per experiment).
     inter_perf_csv: 'blocks-transported-cum.csv'

     # The collated ``.csv`` containing the count of the average # of robots
     # experiencing inter-robot interference for each experiment in the batch (1
     # per experiment).
     interference_count_csv: 'interference-in-cum-avg.csv'

     # The collated ``.csv`` containing the count of the average duration of a
     # robot experiencing inter-robot interference for each experiment in the
     # batch (1 per experiment).
     interference_duration_csv: 'interference-duration-cum-avg.csv'

     # The ``.csv`` file under ``avg_output_leaf`` for each experiment
     # which contains the applied environmental variances.
     tv_environment_csv.: 'tv-environment.csv'

     # The ``.csv``file under ``avg_output_leaf`` for each experiment which
     # contains information about temporally fluctuating populations.
     tv_population_csv: 'tv-population.csv'

``perf.emergence`` sub-dictionary
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The sub-dictionary is optional.

.. code-block:: YAML

   emergence:
     # The weighting factor for task-based emergent self-organization. If it
     # omitted it defaults to 1.0
     alpha_T: 1.0

     # The weighting factor for spatial emergent self-organization. If it is
     # omitted it defaults to 1.0
     alpha_S: 1.0

``perf.flexibility`` sub-dictionary
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: YAML

   flexibility:
     # The weighting factor for the reactivity axis of flexibility. If it
     # omitted it defaults to 1.0.
     alpha_R: 1.0

     # The weighting factor for the adaptability axis of flexibility. If it is
     # omitted it defaults to 1.0.
     alpha_A: 1.0

See also :ref:`Flexibility config <ln-bc-tv-yaml-config>`.

``perf.robustness`` sub-dictionary
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

See :ref:`SAA noise config <ln-bc-saa-noise-yaml-config>`.

Contents of ``config/models.yaml``
----------------------------------

Root level dictionaries:

- ``models`` - List of enabled models. This dictionary is mandatory for all
  simulations.


``models`` dictionary
#####################

.. code-block:: YAML

   models:
     # The name of the python file under ``project/models`` containing one or
     more models meeting the requirements of one of the model interfaces:
     :class:`~models.IConcreteIntraExpModel1D`,
            :class:`~models.IConcreteIntraExpModel2D`,
                   :class:`~models.IConcreteInterExpModel1D`.
     - pyfile: 'my_model1'
     - pyfile: 'my_model2'
     - ...

.. _ln-intra-graphs-line-yaml:

Contents of ``config/intra-graphs-line.yaml``
---------------------------------------------

Root level dictionaries: varies. Each root level dictionary must start with
``LN_``.

``LN_XXX`` sub-dictionary
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: YAML

   graphs:
     # The filename (no path) of the .csv within the simulation output
     # directory for a simulation, sans the .csv extension.
     - src_stem: 'foo'

     # The filename (no path) of the graph to be generated
     # (extension/image type is determined elsewhere). This allows for multiple
     # graphs to be generated from the same ``.csv`` file by plotting different
     # combinations of columns.
     - dest_stem: 'bar'

     # List of names of columns within the source .csv that should be
     # included on the plot. Must match EXACTLY (i.e. no fuzzy matching). Can be
     # omitted to plot all columns within the .csv.
     - cols:
         - 'col1'
         - 'col2'
         - 'col3'
         - '...'

     # The title the graph should have. LaTeX syntax is supported (uses
     # matplotlib after all).
     - title: 'My Title'

     # List of names of the plotted lines within the graph. Can be
     # omitted to set the legend for each column to the name of the column
     # in the ``.csv``.
     - legend:
         - 'Column 1'
         - 'Column 2'
         - 'Column 3'
         - '...'

     # The label of the X-axis of the graph.
     - xlabel: 'X'

     # The label of the Y-axis of the graph.
     - ylabel: 'Y'

Contents of ``config/inter-graphs-line.yaml``
---------------------------------------------

See :ref:`ln-intra-graphs-line-yaml`.

Contents of ``config/intra-graphs-hm.yaml``
---------------------------------------------

Root level dictionaries: varies. Each root level dictionary must start with
``HM_``.

``HM_XXX`` sub-dictionary
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: YAML

   graphs:
     # The filename (no path) of the .csv within the output directory
     # for a simulation to look for the column(s) to plot, sans the .csv
     # extension.
     - src_stem: 'foo.csv'

     # The title the graph should have. LaTeX syntax is supported (uses
     # matplotlib after all).
     - title: 'My Title'
