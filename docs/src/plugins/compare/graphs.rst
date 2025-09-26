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

All configuration for this plugin is in ``<project>/config/graphs.yaml``
file.

.. _plugins/compare/graphs/packages:

OS Packages
===========

Same as for the :ref:`prod.graphs <plugins/prod/graphs>` plugin.

Usage
=====

This plugin can be selected by adding ``compare.graphs`` to ``--compare`` during
stage 5.

.. _plugins/compare/graphs/inter-controller:

Inter-Controller Comparison
===========================

Inter-controller comparison compares the results of multiple controllers on the
same ``--scenario``.  Any collated CSV/graph can be used as a comparison graph!
This includes any additional CSVs that a project creates on its own/by extending
SIERRA via hooks.

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

.. literalinclude:: cc_and_sc.yaml

.. _plugins/compare/graph/inter-scenario:

Inter-Scenario Comparison
=========================

Inter-scenario comparison compares the same ``--controller`` across multiple
``--scenarios``. Only supports univariate batch criteria. Any collated CSV/graph
can be used as a comparison graph! This includes any additional CSVs that a
project creates on its own/by extending SIERRA via hooks.

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

.. literalinclude:: cc_and_sc.yaml
