.. _ln-tutorial-project:

How to Add A New Project
========================

#. Create your project folder somewhere in the filesystem, and link it into
   SIERRA via::

     ln -s /path/to/your/project <sierra_repo>/projects/<project_name>

   Note that ``<project_name>`` does not have to be the same as the name of the
   folder on the filesystem.

   .. IMPORTANT:: SIERRA currently does not have a ``PATH`` inspired mechanism
                  for finding projects specified via ``--project``, so if you
                  don't link your project under ``projects/`` you will get a
                  runtime error.

#. Create the following directory structure within your project directory (or
   copy and modify the one from an existing project).

   - ``config/`` - Plugin YAML configuration root. within this directory, the following
     files are used (not all files are required when running a stage that utilizes
     them):

     - ``main.yaml`` - Main SIERRA configuration file. This file is required for all
       pipeline stages. See :ref:`ln-project-config-main` for documentation.

   - ``controllers.yaml`` - Configuration for controllers (input file/graph
     generation). This file is required for all pipeline stages.See
     :ref:`Controllers YAML config<ln-project-config-controllers>` for documentation.

     - ``intra-graphs-line.yaml`` - Configuration for intra-experiment
       linegraphs. This file is optional. If it is present, graphs defined in it
       will be added to those specified in
       ``core/config/intra-graphs-line.yaml``, and will be generated if stage 4
       is run. See :ref:`Intra-experiment linegraphs YAML config
       <ln-project-config-intra-graphs-line>` for documentation.

     - ``intra-graphs-hm.yaml`` - Configuration for intra-experiment
       heatmaps. This file is optional. If it is present, graphs defined in it
       will be added to those specified in ``core/config/intra-graphs-hm.yaml``,
       and will be generated if stage 4 is run. See :ref:`<Intra-experiment
       heatmaps YAML config <ln-project-config-intra-graphs-hm>` for documentation.

     - ``inter-graphs.yaml`` - Configuration for inter-experiment graphs. This
       file is optional. If it is present, graphs defined in it will be added to
       those specified in ``core/config/inter-graphs-line.yaml``, and will be
       generated if stage 4 is run. See :ref:`Inter-experiment lingraphs YAML
       config <ln-project-config-inter-graphs-line>` for documentation.

     - ``stage5.yaml`` - Configuration for stage5 controller comparisons. This file
       is required if stage5 is run, and optional otherwise. See
       :ref:`ln-project-config-stage5` for documentation.

     - ``models.yaml`` - Configuration for intra- and inter-experiment
       models. This file is optional. If it is present, models defined and
       enabled in it will be run before stage 4 intra- and/or inter-experiment
       graph generation, if stage 4 is run. See :ref:`ln-project-config-models`
       for documentation.

   - ``generators/scenario_generators.py`` - Specifies extensions/specializations
     of the foraging scenarios in the SIERRA core, as well as any other scenarios
     the user would want to be able to pass via the ``--scenario`` cmdline
     argument.

   - ``variables/`` - Additional variables (including batch criteria) defined by
     the plugin/project that can be directly or indirectly used by the
     ``--batch-criteria`` and ``--scenario`` cmdline arguments.

   - ``cmdline.py`` - Specifies cmdline extensions specific to the plugin/project.

#. Read the docs on what each of the configuration files is for.

.. _ln-project-config-main:

``config/main.yaml``
--------------------

An example main configuration file:

.. code-block:: YAML

   # Configuration for each ARGoS simulation run. This dictionary is
   # mandatory for all simulations.
   sim:
     # The directory within each simulation's working directory which will
     # contain the metrics output as by the simulation. This key is mandatory
     # for all simulations.
     sim_metrics_leaf: 'metrics'

     # The directory within each simulation's working directory which will
     # contain the frames output by ARGoS during simulation, if frame grabbing
     # is configured. This key is currently mandatory for all simulations, even
     # if rendering/frame grabbing is not employed.
     argos_frames_leaf: 'frames'

   # Configuration for SIERRA internals. This dictionary is mandatory
   # for all simulations.
   sierra:
     # The directory within the output directory for each experiment within
     # the batch where the frames created from the ``.csv`` files created by the
     # selected project will be stored for rendering. This key is currently
     # mandatory for all simulations, even if rendering/frame grabbing is
     # is not employed.
     project_frames_leaf: 'project-frames'

   # Configuration for performance measures. This key-value pair is mandatory
   # for all simulations. The value is the location of the .yaml configuration
   # file for performance measures. It is a separate config file so that multiple
   # scenarios within a single project which define performance measures in
   # different ways can be easily accomodated.
   perf: 'perf-config.yaml'


``perf`` dictionary
###################

Within the pointed-to .yaml file for ``perf`` configuration, the structure is:

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

     # The ``.csv`` file under ``statistics_leaf`` for each experiment which
     # contains the averaged performance information for the experiment.
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

     # The ``.csv`` file under ``statistics_leaf`` for each experiment
     # which contains the average applied environmental variances.
     tv_environment_csv.: 'tv-environment.csv'

     # The ``.csv``file under ``statistics_leaf`` for each experiment which
     # contains averaged information about temporally fluctuating populations.
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

.. _ln-project-config-controllers:

``config/controllers.yaml``
---------------------------

Root level dictionaries: varies; project dependent. Each root level dictionary
is treated as the name of a controller `category` when ``--controller`` is
parsed. For example, if you pass ``--controller=mycategory.FizzBuzz`` to SIERRA,
then you need to have a root level dictionary ``mycategory`` defined in
``controllers.yaml``.

``<controller_category>`` dictionary
####################################

A complete category YAML configuration for a controller category ``mycategory``
is as follows; components explained in the subsections that follow.

.. code-block:: YAML

   mycategory:
     # XML changes which should be made to the template `.argos` file for `all`
     # controllers in the category. This is usually things like setting ARGoS loop
     # functions appropriately, if required. Each change is formatted as a list:
     # [parent tag, tag, value, each specified in the XPath syntax.
     #
     # This section can be omitted if not needed. If ``--argos-rendering`` is
     # passed, then this section should be used to specify the QT visualization
     # functions to use.
     xml:
       attr_change:
         - ['.//loop-functions', 'label', 'my_category_loop_functions']
         - ['.//qt-opengl/user_functions', 'label', 'my_category_qt_loop_functions']

     # Under ``controllers`` is a list of controllers which can be passed as part
     # of ``--controller`` when invoking SIERRA, matched by ``name``. Any
     # controller-specific XML attribute changes can be specified here, with the
     # same syntax as the changes for the controller category.

     controllers:
       - name: FizzBuzz
         xml:
           attr_change:

             # The ``__controller__`` tag in the template input file which is
             # arbitrary, and any string will do. It's purpose is to allow the same
             # template input file to be used by multiple controller types. If you
             # don't need that, then you can omit the ``xml``/ ``attr_change`` tags
             # in your configuration altogether.
             - ['.//controllers', '__controller___', 'FizzBuzz']

         # Sets of graphs common to multiple controller categories can be
         # inherited with the ``graphs_inherit`` dictionary; see the YAML docs for
         # details on how to include named lists inside other lists.
         graphs_inherit:
           - *base_graphs

         # Specifies a list of graph categories from inter- or
         # intra-experiment ``.yaml`` configuration which should be generated
         # for this controller, if the necessary input .csv files exist.
         graphs: &MyController_graphs
           - GraphCategory1
           - GraphCategory2

.. _ln-project-config-models:

``config/models.yaml``
----------------------

Root level dictionaries:

- ``models`` - List of enabled models. This dictionary is mandatory for all
  simulations.


``models`` dictionary
#####################

.. code-block:: YAML

   models:

     # The name of the python file under ``project/models`` containing one or
     # more models meeting the requirements of one of the model interfaces:
     # :class:`~models.IConcreteIntraExpModel1D`,
     # :class:`~models.IConcreteIntraExpModel2D`,
     # :class:`~models.IConcreteInterExpModel1D`.

     - pyfile: 'my_model1'
     - pyfile: 'my_model2'
       model2_param1: 17
       ...
     - ...

Any other parameters/dictionaries/etc needed by a particular model can be added
to the list above and they will be passed through to the model's constructor.

.. _ln-project-config-intra-graphs-line:

``config/intra-graphs-line.yaml``
---------------------------------

Root level dictionaries: varies. Each root level dictionary must start with
``LN_``.

``LN_XXX`` sub-dictionary
#########################

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


.. _ln-project-config-inter-graphs-line:

``config/inter-graphs-line.yaml``
---------------------------------

See :ref:`ln-project-config-intra-graphs-line`. Each inter-experiment linegraph
has an additional field ``summary`` which determines in the generated graph is a
:class:`~core.graphs.summary_line_graph95.SummaryLineGraph95` or a
:class:`~core.graphs.stacked_line_graph.StackedLineGraph` (default if omitted).

.. _ln-project-config-intra-graphs-hm:

``config/intra-graphs-hm.yaml``
-------------------------------

Root level dictionaries: varies. Each root level dictionary must start with
``HM_``.

``HM_XXX`` sub-dictionary
#########################

.. code-block:: YAML

   graphs:
     # The filename (no path) of the .csv within the output directory
     # for a simulation to look for the column(s) to plot, sans the .csv
     # extension.
     - src_stem: 'foo.csv'

     # The title the graph should have. LaTeX syntax is supported (uses
     # matplotlib after all).
     - title: 'My Title'
