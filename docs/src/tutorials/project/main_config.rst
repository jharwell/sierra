.. _ln-tutorials-project-main-config:

==================
Main Configuration
==================

The three main configuration files that you must define so that SIERRA knows how
to interact with your project are:

- ``config/main.yaml`` - Main configuration.

- ``config/perf-config.yaml`` - Configuration for summary performance
  measures. Does not have to be named ``perf-config.yaml``; see below.

- ``config/controllers.yaml`` - Configuration for robot controllers.

Main Configuration File: ``config/main.yaml``
=============================================

An example main configuration file:

.. code-block:: YAML

   # Configuration for each ARGoS simulation run. This dictionary is
   # mandatory for all simulations.
   sim:
     # The directory within each simulation's working directory which will
     # contain the metrics output as by the simulation. This key is mandatory
     # for all simulations.
     sim_metrics_leaf: 'metrics'

   # Configuration for SIERRA internals. This dictionary is mandatory
   # for all simulations.
   sierra:
     # Configuration for performance measures. This key-value pair is mandatory
     # for all simulations. The value is the location of the .yaml
     # configuration file for performance measures. It is a separate config
     # file so that multiple scenarios within a single project which define
     # performance measures in  different ways can be easily accomodated.
     perf: 'perf-config.yaml'

Summary Performance Measures Configuration File
===============================================

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
     raw_perf_ylabel: '\# Blocks'

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

Controllers Configuration File: ``config/controllers.yaml``
===========================================================

Root level dictionaries: varies; project dependent. Each root level dictionary
is treated as the name of a controller `category` when ``--controller`` is
parsed. For example, if you pass ``--controller=mycategory.FizzBuzz`` to SIERRA,
then you need to have a root level dictionary ``mycategory`` defined in
``controllers.yaml``.

Example YAML Config
^^^^^^^^^^^^^^^^^^^

ppA complete YAML configuration for a controller category ``mycategory`` and a
controller ``FizzBuzz``. This configuration specifies that all graphs in the
categories of ``LN_MyCategory1``, ``LN_MyCategory2``, ``HM_MyCategory1``,
``HM_MyCategory2`` are applicable to ``FizzBuzz``, and should be generated if
the necessary simulation output files exist. The ``LN_MyCategory1``,
``LN_MyCategory2`` graph categories are common to multiple controllers in this
project, while the ``HM_MyCategory1``, ``HM_MyCategory2`` graph categories are
specific to the ``FizzBuzz`` controller.

.. code-block:: YAML

   my_base_graphs:
     - LN_MyCategory1
     - LN_MyCategory2

   mycategory:
     # XML changes which should be made to the template ``.argos`` file for
     # *all* controllers in the category. This is usually things like setting
     # ARGoS loop functions appropriately, if required. Each change is formatted
     # as a list: [parent tag, tag, value] each specified in the XPath syntax.
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

             # The ``__controller__`` tag in the ``--template-input-file`` is
             # REQUIRED. It's purpose is to allow the same template input file to
             # be used by multiple controller types and to allow SIERRA to
             # automatically populate the library name that ARGoS will look for to
             # find the controller # C++ code based on the ``--project`` name .

             - ['.//controllers', '__controller___', 'FizzBuzz']

         # Sets of graphs common to multiple controller categories can be
         # inherited with the ``graphs_inherit`` dictionary (they are added to
         # the ``graphs`` dictionary); this dictionary is optional, but is handy
         # to reduce repetive declarations and typing. see the YAML docs for
         # details on how to include named lists inside other lists.
         graphs_inherit:
           - *my_base_graphs

         # Specifies a list of graph categories from inter- or
         # intra-experiment ``.yaml`` configuration which should be generated
         # for this controller, if the necessary input .csv files exist.
         graphs: &FizzBuzz_graphs
           - HM_MyCategory1
           - HM_MyCategory2
