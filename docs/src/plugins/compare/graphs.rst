.. _plugins/compare/graphs:

================
Graph Comparison
================

.. IMPORTANT:: Only :term:`Batch Summary Data` files can be used as inputs to
               comparison with this plugin.

This page has the following sections:

- `Inter-Controller Comparison`_: How to generate comparison graphs for a set of
  controllers which have all been run on the *same* scenario and :term:`Batch Criteria`.

- `Inter-Scenario Comparison`_: How to generate comparison graphs for a single
  controller which has been run across *multiple* scenarios using the same
  :term:`Batch Criteria`.

- `Inter-Batch Comparison`_: How to generate comparison graphs for multiple
  :term:`Batch Criteria` which have been run on the *same* scenario using the
  same controller.

All configuration for stage 5 is in ``<project>/config/stage5.yaml`` file. This
file is mandatory for running stage 5, and optional otherwise.

Usage
=====

This plugin can be selected by adding ``compare.graphs`` to ``--compare`` during
stage 5.

.. _plugins/compare/graphs/inter-controller:

Inter-Controller Comparison
===========================

Inter-controller comparison compares the results of multiple controllers on the
same ``--scenario``. An example ``stage5.yaml``, defining two different
comparison graphs is shown below.

.. NOTE:: Any collated CSV/graph can be used as a comparison graph! This
          includes any additional CSVs that a project creates on its own/by
          extending SIERRA via hooks.


When active, this comparison type will create the following directory tree. For
the purposes of explanation, I will use the following partial SIERRA option sets
to explain the additions to the experiment tree for stage 5::

  --pipeline 5 \
  --controller-comparison \
  --batch-criteria population_size.Log8 \
  --controllers-list d0.CRW,d0.DPO \
  --sierra-root=$HOME/exp"


This invocation will cause SIERRA to create the following directory structure as
it runs::


  $HOME/exp
     |-- d0.CRW+d0.DPO-cc-csvs/
     |-- d0.CRW+d0.DPO-cc-graphs/

``d0.CRW+d0.DPO-cc-graphs/`` is the directory holding the comparison graphs for
each scenario for which ``d0.CRW`` and ``d0.DPO`` were run (scenarios are
computed by examining the directory tree for stages 1-4). Controller names are
arbitrary for the purposes of stage 5 and entirely depend on the
project). ``d0.CRW+d0.DPO-cc-csvs/`` are the :term:`Inter-Batch Data` files used
to create the graphs.

Graph YAML Config
-----------------

Unless stated otherwise, all keys are required.

.. code-block:: YAML

   # Inter-controller comparison: For a set of controllers which have all been
   # run in the same scenario.
   inter-controller:
     # The filename (no path, extension) of the .csv within the collated .csv
     # output directory for each batch experiment which contains the information
     # to collate across controllers/scenarios.
     #
     # The src_stem must match the dest_stem from an inter-experiment line graph
     # in order to generate the comparison graph!
     #
     # Note that if you are using bivariate batch criteria + intra-scenario
     # comparison, you *may* have to append the interval # to the end of the
     # stem, because collated 2D CSV files form a temporal sequence over the
     # duration of the experiment. If you forget to do this, you will get a
     # warning and no graph will be generated, because SIERRA won't know which
     # 2D csv you want to us as source. Frequently you are interested in steady
     # state behavior, so putting 'n_intervals - 1' is desired.
     #
     # If the src_stem is from a CSV you generated outside of the SIERRA
     # core/via a hook, then this restriction does not apply.
     - src_stem: PM-ss-raw

       # The filename (no path, extent) of the .csv file within the
       # controller/scenario comparison directory in ``--sierra-root`` (outside
       # of the directories for each controller/scenario!) which should contain
       # the data collated from each batch experiment. I usually put a prefix
       # such as ``cc`` (controller comparison) to help distinguish these graphs
       # from the collated graphs in stage 4.
       dest_stem: cc-PM-ss-raw

       # The title the graph should have. This cannot be computed from the batch
       # criteria in general in stage 5, because you can comparison results
       # across scenarios which use different batch criteria. This key is
       # optional.
       title: ''

       # The Y or Z label of the graph (depending on the type of comparison
       # graph selected on the cmdline). This key is optional.
       label: 'Avg. Object Collection Rate'

       # For bivariate batch criteria, select which criteria should be on the X
       # axis if the comparison graphs are linegraphs. 0=criteria1,
       # 1=criteria2. Ignored for univariate batch criteria or if heatmaps are
       # selected for as the comparison type. This key is optional, and
       # defaults to 0 if omitted.
       primary_axis: 0

      # The experiments from each batch experiment which should be included on
      # the comparison graph. This is useful to exclude exp0 (for example), if
      # you are interested in behavior under non-ideal conditions and exp0
      # contains behavior under ideal conditions as the "base case" in the
      # batch. Syntax is parsed as a python slice, so as ``X:Y`` as you would
      # expect. This key is optional, and defaults to ``:`` if omitted.
       include_exp: '2:'


.. _plugins/compare/graph/inter-scenario:

Inter-Scenario Comparison
=========================

Inter-scenario comparison compares the same ``--controller`` across multiple
``--scenarios``. An example ``stage5.yaml``, defining a comparison
graphs is shown below. Only supports univariate batch criteria.

.. NOTE:: Any collated CSV/graph can be used as a comparison graph! This
          includes any additional CSVs that a project creates on its own/by
          extending SIERRA via hooks.

When active, this comparison type will create the following directory tree. For
the purposes of explanation, I will use the following partial SIERRA option sets
to explain the additions to the experiment tree for stage 5::

   --pipeline 5 \
   --scenario-comparison \
   --batch-criteria population_size.Log8 \
   --scenarios-list=RN.16x16x2,PL.16x16x2 \
   --sierra-root=$HOME/exp"


This invocation will cause SIERRA to create the following directory structure as
it runs::

  $HOME/exp/
     |-- RN.16x16x2+PL.16x16x2-sc-graphs/
     |-- RN.16x16x2+PL.16x16x2-sc-csvs/


``RN.16x16x2+PL.16x16x2-sc-graphs/`` is the directory holding the comparison
graphs for all controllers which were previously run on the scenarios
``RN.16x16x2`` and ``PL.16x16x2`` (scenario names are arbitrary for the purposes
of stage 5 and entirely depend on the
project). ``RN.16x16x2+PL.16x16x2-sc-csvs/`` are the :term:`Inter-Batch Data`
files used to create the graphs.


Graph YAML Config
-----------------

Same syntax and meaning as the configuration for inter-controller comparison
graphs.

.. code-block:: YAML

   inter-scenario:
     graphs:
       # raw performance
       - src_stem: PM-ss-raw
         dest_stem: cc-PM-ss-raw
         title: ''
         label: 'Avg. Object Collection Rate'
         primary_axis: 0
         include_exp: '2:'
