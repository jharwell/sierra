.. _ln-tutorials-project-main-config:

==================
Main Configuration
==================

The three main required configuration files that you must define so that SIERRA
knows how to interact with your project are:

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
     # for all simulations. Can be anything; this is the interface link between
     # where the C++ code outputs things and where SIERRA looks for outputs.
     sim_metrics_leaf: 'metrics'

   # Configuration for performance measures. This key-value pair is mandatory
   # for all simulations. The value is the location of the .yaml
   # configuration file for performance measures. It is a separate config
   # file so that multiple scenarios within a single project which define
   # performance measures in  different ways can be easily accommodated.
   perf: 'perf-config.yaml'

Summary Performance Measures Configuration File
===============================================

Within the pointed-to .yaml file for ``perf`` configuration, the basic structure
is:

.. code-block:: YAML

   perf:

     # Is the performance measure for the project inverted, meaning that lower
     # values are better (as opposed to higher values, which is the default if
     # this is omitted)? This key is optional.
     inverted: true

     # The ``.csv`` file under ``statistics/`` for each experiment which
     # contains the averaged performance information for the experiment. This
     # key is mandatory.
     intra_perf_csv: 'block-transport.csv'

     # The ``.csv`` column within ``intra_perf_csv`` which is the
     # temporally charted performance measure for the experiment. This key is
     # mandatory.
     intra_perf_col: 'cum_avg_transported'

Additional fields can be added to this dictionary as needed to support custom
performance measures,graph generation, or batch criteria as needed. See
:ref:`ln-bc-saa-noise-yaml-config` for an example of adding fields to this
dictionary as a lookup table of sorts for a broader range of cmdline
configuration (i.e., using it to make the cmdline syntax for the
`ln-bc-saa-noise` much nicer).

Controllers Configuration File: ``config/controllers.yaml``
===========================================================

Root level dictionaries: varies; project dependent. Each root level dictionary
is treated as the name of a :term:`Controller Category` when ``--controller`` is
parsed. For example, if you pass ``--controller=mycategory.FizzBuzz`` to SIERRA,
then you need to have a root level dictionary ``mycategory`` defined in
``controllers.yaml``.

Example YAML Config
^^^^^^^^^^^^^^^^^^^

A complete YAML configuration for a :term:`Controller Category` ``mycategory``
and a controller ``FizzBuzz``. This configuration specifies that all graphs in
the categories of ``LN_MyCategory1``, ``LN_MyCategory2``, ``HM_MyCategory1``,
``HM_MyCategory2`` are applicable to ``FizzBuzz``, and should be generated if
the necessary simulation output files exist. The ``LN_MyCategory1``,
``LN_MyCategory2`` graph categories are common to multiple controllers in this
project, while the ``HM_MyCategory1``, ``HM_MyCategory2`` :term:`graph
categories<Graph Category>` are specific to the ``FizzBuzz`` controller.

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
     # This section is optional. If ``--argos-rendering`` is passed, then this
     # section should be used to specify the QT visualization functions to use.
     xml:
       attr_change:
         - ['.//loop-functions', 'label', 'my_category_loop_functions']
         - ['.//qt-opengl/user_functions', 'label', 'my_category_qt_loop_functions']

     # Under ``controllers`` is a list of controllers which can be passed as part
     # of ``--controller`` when invoking SIERRA, matched by ``name``. Any
     # controller-specific XML attribute changes can be specified here, with the
     # same syntax as the changes for the controller category (``mycategory`` in
     # this example)
     controllers:
       - name: FizzBuzz
         xml:
           attr_change:

             # The ``__controller__`` tag in the ``--template-input-file`` is
             # REQUIRED. It's purpose is to allow the same template input file to
             # be used by multiple controller types and to allow SIERRA to
             # automatically populate the library name that ARGoS will look for to
             # find the controller C++ code based on the ``--project`` name .
             - ['.//controllers', '__controller___', 'FizzBuzz']

         # Sets of graphs common to multiple controller categories can be
         # inherited with the ``graphs_inherit`` dictionary (they are added to
         # the ``graphs`` dictionary); this dictionary is optional, but is handy
         # to reduce repetitive declarations and typing. see the YAML docs for
         # details on how to include named lists inside other lists.
         graphs_inherit:
           - *my_base_graphs

         # Specifies a list of graph categories from inter- or
         # intra-experiment ``.yaml`` configuration which should be generated
         # for this controller, if the necessary input .csv files exist.
         graphs: &FizzBuzz_graphs
           - HM_MyCategory1
           - HM_MyCategory2
