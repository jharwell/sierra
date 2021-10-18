.. _ln-tutorials-project-stage5-config:

=====================
Stage 5 Configuration
=====================

This page has the following sections:

- How to generate comparison graphs for a set of controllers
  which have all been run on the `same` scenario(s).

- How to generate comparison graphs for a single controller which has been run
  across `multiple` scenarios.

All configuration for stage 5 is in ``<project>/config/stage5.yaml`` file. This
file is mandatory for running stage 5 (duh).


Intra-Scenario Comparison
=========================

Intra-scenario comparison compares the results of multiple controllers on the
same ``--scenario``. An example ``stage5.yaml``, defining two different
comparison graphs is shown below.

.. NOTE:: Any collated .csv/graph can be used as a comparison graph!

.. code-block:: YAML

   intra_scenario:
     graphs:
       # raw performance
       - src_stem: PM-ss-raw
         dest_stem: cc-PM-ss-raw
         title: ''
         label: 'Avg. Object Collection Rate'
         primary_axis: 0
         include_exp: '2:'

       # scalability
       - src_stem: PM-ss-scalability-parallel-frac
         dest_stem: cc-PM-ss-scalability-parallel-frac
         title: ''
         label: 'Scalability Value'
         primary_axis: 0
         include_exp: '2:'


Graph YAML Config
-----------------

Unless stated otherwise, all keys are mandatory.

.. code-block:: YAML

   graphs:
     # The filename (no path, extension) of the .csv within the collated .csv
     # output directory for each batch experiment which contains the information
     # to  collate across controllers/scenarios.
     - src_stem: PM-ss-raw

       # The filename (no path, extent) of the .csv file within the
       # controller/scenario comparison directory in ``--sierra-root`` (outside of
       # the directories for each controller/scenario!) which should contain the
       # data collated from each batch experiment. I usually put a prefix such
       # as ``cc`` (controller comparison) to help distinguish these graphs from
       # the collated graphs in stage 4.
       dest_stem: cc-PM-ss-raw

       # The title the graph should have. This cannot be computed from the batch
       # criteria in general in stage 5, because you can comparison results across
       # scenarios which use different batch criteria.
       title: ''

       # The Y or Z label of the graph (depending on the type of comparison
       # graph selected on the cmdline).
       label: 'Avg. Object Collection Rate'

       # For bivariate batch criteria, select which criteria should be on the X
       # axis if the comparison graphs are linegraphs. 0=criteria1,
       # 1=criteria2. Ignored for univariate batch criteria or if heatmaps are
       # selected for as the comparison type.
       primary_axis: 0

       # The experiments from each batch experiment which should be included on
       # the comparison graph. This is useful to exclude exp0 (for example), if
       # you are interested in behavior under non-ideal conditions and exp0
       # contains behavior under ideal conditions as the "base case" in the
       # batch. Syntax is parsed as a python slice, so as ``X:Y`` as you would
       # expect. This key is optional, and defaults to ``:`` if omitted.
       include_exp: '2:'


Inter-Scenario Comparison
=========================

Inter-scenario comparison compares the same ``--controller`` across multiple
``--scenarios``. An example ``stage5.yaml``, defining two different comparison
graphs is shown below.

.. NOTE:: Any collated .csv/graph can be used as a comparison graph!

.. code-block:: YAML

   inter_scenario:
     graphs:
       # raw performance
       - src_stem: PM-ss-raw
         dest_stem: cc-PM-ss-raw
         title: ''
         label: 'Avg. Object Collection Rate'
         primary_axis: 0
         include_exp: '2:'


Graph YAML Config
-----------------

Same syntax and meaning as the configuration for intra-scenario comparison
graphs.
