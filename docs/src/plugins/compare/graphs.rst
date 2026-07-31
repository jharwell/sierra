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

This plugin performs stage-5 :term:`Data Collation`: it takes the per-batch
:term:`Collated Output Data` for each compared thing (controller or scenario)
and places them side by side -- one column per compared thing, indexed by
experiment -- in a single :term:`Inter-Batch Data` file per measure. For a
visualization of this reshape, see :ref:`concepts/dataflow/stage5`.

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

.. _plugins/compare/graphs/model-overlay:

Model Overlay
-------------

If models were run during stage 4 (i.e., the ``proc.modelrunner``
processor was included in ``--proc``), and an inter-experiment model targets the
same ``src`` as a comparison graph, then the model's predictions are
collated alongside the empirical data and **overlaid on the comparison graph**
as an additional line per compared thing. This works for both inter-controller
and inter-scenario comparison, and for univariate batch criteria.

The collated predictions and their legends are written to the ``-cc-models`` /
``-sc-models`` directory (see the trees below). No extra configuration is
required beyond having run the models in stage 4: the overlay is keyed off the
comparison graph's ``src``, so a model whose target matches that path is
picked up automatically. If no matching model output exists, the comparison
graph is generated normally without an overlay.

.. NOTE:: Model overlay is currently supported for univariate batch criteria
          only. For bivariate batch criteria the comparison graphs are generated
          without a model overlay even if models were run.

.. _plugins/compare/graphs/exp-selection:

Experiment Selection (``include_exp``)
--------------------------------------

The ``include_exp`` key (see the YAML config below) selects which experiments
from each batch are included on a comparison graph, as a python-style slice. The
selection is applied **consistently to everything on the graph**: the collated
data, any overlaid model predictions, and the graph's X-axis ticks are
all filtered identically. As a result the collated ``.csv``, the collated
``.model`` (if any), and the plotted axes always have the same set of
experiments, for both inter-controller and inter-scenario comparison.

For example, ``include_exp: '1:'`` on a batch of three experiments drops the
first experiment, leaving two data rows, two model rows (if a model was
overlaid), and two X-axis ticks.

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
  --things=d0.CRW,d0.DPO \
  --sierra-root=$HOME/exp


This invocation will cause SIERRA to create the following directory structure as
it runs::


  $HOME/exp
     |-- d0.CRW+d0.DPO-cc-csvs/
     |-- d0.CRW+d0.DPO-cc-graphs/
     |-- d0.CRW+d0.DPO-cc-models/

``d0.CRW+d0.DPO-cc-graphs/`` is the directory holding the comparison graphs for
each scenario for which ``d0.CRW`` and ``d0.DPO`` were run (scenarios are
computed by examining the directory tree for stages 1-4). Controller names are
arbitrary for the purposes of stage 5 and entirely depend on the
project). ``d0.CRW+d0.DPO-cc-csvs/`` are the files used to create the graphs.
``d0.CRW+d0.DPO-cc-models/`` holds collated model predictions, and is populated
only when stage-4 inter-experiment models were run for the compared
measures. When present, these predictions are also **overlaid** on the
corresponding comparison graphs (see `Model Overlay`_).

Graph YAML Config
-----------------

Comparison graphs live under the ``inter-controller`` key in
``<project>/config/graphs.yaml``. Unlike the ``intra-exp``/``inter-exp``
sections used by the :ref:`prod.graphs <plugins/prod/graphs>` plugin, this
section is a **flat list** of graphs with no category level, because the things
being compared are named directly on the cmdline rather than being
enabled/disabled via controller YAML.

``src``, ``dest`` and ``type`` are required; everything else is
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
   --controller=d0.DPO \
   --things=RN.16x16x2,PL.16x16x2 \
   --sierra-root=$HOME/exp


This invocation will cause SIERRA to create the following directory structure as
it runs::

  $HOME/exp/
     |-- RN.16x16x2+PL.16x16x2-sc-graphs/
     |-- RN.16x16x2+PL.16x16x2-sc-csvs/
     |-- RN.16x16x2+PL.16x16x2-sc-models/


``RN.16x16x2+PL.16x16x2-sc-graphs/`` is the directory holding the comparison
graphs for the single ``--controller`` (here ``d0.DPO``) which was previously
run on the scenarios ``RN.16x16x2`` and ``PL.16x16x2`` (scenario names are
arbitrary for the purposes of stage 5 and entirely depend on the
project). ``RN.16x16x2+PL.16x16x2-sc-csvs/`` are the :term:`Inter-Batch Data`
files used to create the graphs. ``RN.16x16x2+PL.16x16x2-sc-models/`` holds
collated model predictions, and is populated only when stage-4 inter-experiment
models were run for the compared measures. When present, these predictions are
also **overlaid** on the corresponding comparison graphs (see `Model
Overlay`_).


Graph YAML Config
-----------------

Same syntax and meaning as the configuration for inter-controller comparison
graphs, but under the ``inter-scenario`` key rather than ``inter-controller``.
The example below shows the inter-controller form; substitute the section name
for inter-scenario comparison.

.. literalinclude:: cc_and_sc.yaml
