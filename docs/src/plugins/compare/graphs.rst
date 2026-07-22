.. _plugins/compare/graphs:

================
Graph Comparison
================

.. IMPORTANT:: Only :term:`Batch Summary Data` files can be used as inputs to
               comparison with this plugin.

This page has the following sections:

- `Inter-Controller Comparison`_: How to generate comparison graphs for a set of
  controllers which have all been run on a *single* scenario and :term:`Batch
  Criteria`.

- `Inter-Scenario Comparison`_: How to generate comparison graphs for a *set* of
  scenarios which have all been run using a *single* controller and :term:`Batch
  Criteria`.

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

Cmdline Interface
-----------------

.. sphinx_argparse_cli::
   :module: sierra.plugins.compare.graphs.cmdline
   :func: sphinx_cmdline_stage5
   :prog: sierra

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
  --across=controllers \
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
project). ``d0.CRW+d0.DPO-cc-csvs/`` are the files used to create the graphs.

Graph YAML Config
-----------------

Comparison graphs live under the ``inter-controller`` key in
``<project>/config/graphs.yaml``. Unlike the ``intra-exp``/``inter-exp``
sections used by the :ref:`prod.graphs <plugins/prod/graphs>` plugin, this
section is a **flat list** of graphs with no category level, because the things
being compared are named directly on the cmdline rather than being
enabled/disabled via controller YAML.

``src_stem``, ``dest_stem`` and ``type`` are required; everything else is
optional and defaults as noted below.

.. IMPORTANT:: Comparison graphs use ``type: comparison_line``, which is
               **not** the same as the ``summary_line`` type used by
               ``prod.graphs``, despite both rendering as lines. A
               ``summary_line`` plots one point per :term:`Experiment` within a
               single batch; a ``comparison_line`` plots one line per
               controller (or scenario) *across* batches. The two accept nearly
               disjoint key sets, and are validated by different schemas.

               .. versionchanged:: 1.5.12
                  Renamed from ``summary_line``, which collided with the
                  ``prod.graphs`` type of the same name. Existing configs must
                  be updated.

.. literalinclude:: cc_and_sc.yaml

.. _plugins/compare/graphs/inter-scenario:

Inter-Scenario Comparison
=========================

Inter-scenario comparison compares the same ``--controller`` across multiple
scenarios. Only supports univariate batch criteria. Any collated CSV/graph can
be used as a comparison graph! This includes any additional CSVs that a project
creates on its own/by extending SIERRA via hooks.

When active, this comparison type will create the following directory tree. For
the purposes of explanation, I will use the following partial SIERRA option sets
to explain the additions to the experiment tree for stage 5::

   --pipeline 5 \
   --across=scenarios \
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
graphs, but under the ``inter-scenario`` key rather than ``inter-controller``.
The example below shows the inter-controller form; substitute the section name
for inter-scenario comparison.

.. literalinclude:: cc_and_sc.yaml
