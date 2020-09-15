How to Add A New Plugin (I mean project)
========================================

The argument to the cmdline option ``--project`` is added to the path
``plugins/<option>``, and the plugin directory tree must have the following
structure and content (a subset of the SIERRA core directory structure):

- ``config/`` - Plugin YAML configuration root. within this directory, the following
  files must be present when running a stage that utilizes them:

  - ``main.yaml`` - Main SIERRA configuration file. This file is required for all
    pipeline stages.

  - ``controllers.yaml`` - Configuration for controllers (input file/graph
    generation). This file is required for all pipeline stages.

  - ``intra-graphs-line.yaml`` - Configuration for intra-experiment
    linegraphs. This file is optional. If it is present, graphs defined in it
    will be added to those specified in ``core/config/intra-graphs-line.yaml``,
    and will be generated if stage 4 is run.

  - ``intra-graphs-line.yaml`` - Configuration for intra-experiment
    heatmaps. This file is optional. If it is present, graphs defined in it will
    be added to those specified in ``core/config/intra-graphs-hm.yaml``, and
    will be generated if stage 4 is run.

  - ``inter-graphs.yaml`` - Configuration for inter-experiment graphs. This file
    is optional. If it is present, graphs defined in it will be added to those
    specified in ``core/config/inter-graphs-line.yaml``, and will be generated
    if stage 4 is run.

  - ``stage5.yaml`` - Configuration for stage5 controller comparisons. This file
    is required if stage5 is run, and optional otherwise.

- ``generators/scenario_generators.py`` - Specifies extensions/specializations
  of the foraging scenarios in the SIERRA core, as well as any other scenarios
  the user would want to be able to pass via the ``--scenario`` cmdline
  argument.

- ``variables/`` - Additional variables (including batch criteria) defined by
  the plugin/project that can be directly or indirectly used by the
  ``--batch-criteria`` and ``--scenario`` cmdline arguments.

- ``cmdline.py`` - Specifies cmdline extensions specific to the plugin/project.

Contents of ``main.yaml``
-------------------------

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

.. code-block:: YAML

   emergence:
     # The weighting factor for task-based emergent self-organization. If it
     # omitted it defaults to 0.5.
     alpha_T: 0.50

     # The weighting factor for spatial emergent self-organization. If it is
     # omitted it defaults to 0.5.
     alpha_S: 0.50

``perf.flexibility`` sub-dictionary
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: YAML

   flexibility:
     # The weighting factor for the reactivity axis of flexibility. If it
     # omitted it defaults to 0.5.
     alpha_R: 0.50

     # The weighting factor for the adaptability axis of flexibility. If it is
     # omitted it defaults to 0.5.
     alpha_A: 0.50

See also :ref:`Flexibility config <ln-bc-tv-yaml-config>`.

``perf.robustness`` sub-dictionary
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

See :ref:`SAA noise config <ln-bc-saa-noise-yaml-config>`.
