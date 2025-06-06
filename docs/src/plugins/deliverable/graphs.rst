.. _plugins/deliverable/graphs:

=======================
Static Graph Generation
=======================

This plugin generates static graphs using holoviews+matplotlib during
stage 4. It has the following stage 3 plugin requirements:

- :ref:`plugins/proc/stat` (all graphs)

Usage
=====

.. TODO:: fill in CLI interface here once it is pulled out.

This plugin supports two types of graphs, and therefore two types of analyses:

- Intra-experiment graphs, which can be thought of as graphs generated directly
  from the aggregated data from a set of :term:`Experimental Runs <Experimental
  Run>`.

- Inter-experiment graphs, which are generated from a selected subset of data
  from each :term:`Experiment` in a :term:`Batch Experiment`.

.. list-table::
   :header-rows: 1

   * - Graph Type

     - Use Case Characteristics

   * - Linegraph

     -

       - The data you want to graph can be represented by a line (i.e. is one
         dimensional in some way). Time series are a graph example of this.

       - The data you want to graph can be obtained from a single .csv file
         (multiple columns in the same CSV file can be graphed simultaneously).

       - You need/want statistical distribution information to be shown on the
         graphs to help determine statistical significance.

       - The data you want to graph can be obtained from a single column from a
         single CSV file.

       - The data you want to graph requires comparison between multiple
         experiments in a batch.

   * - Heatmap

     -

       - The data you want to graph is two dimensional (e.g. a spatial
         representation of the arena is some way).

       - You don't need/aren't interested in statistics.

Configuration
=============

This plugin is mostly configured via a ``graphs.YAML`` in the :term:`Project`
config root. The file is structured as follows:

.. code-block:: YAML

    intra-exp:
       mycategory1:
         - ...
         - ...
         - ...
     inter-exp:
       mycategory2:
         - ...
         - ...
         - ...


.. IMPORTANT:: Because SIERRA tells uv -> matplotlib to use LaTeX internally to
               generate graph labels, titles, etc., the standard LaTeX character
               restrictions within strings apply to all fields (e.g., '#' is
               illegal but '\#' is OK).

Intra-experiment graphs and inter-experiment graphs are configured in their
corresponding sections as shown. Within each intra-/inter- experiment graph
section is a set of categories, and within each category is list of graphs to
generate, specified in a declarative way. Categories can be named anything, and
serve two purposes:

- A nice way to logically cluster your graphs into related semantic groups.

- Act as a filtering mechanism in conjunction with the ``controllers.yaml`` file
  to tell SIERRA what graphs to generate for what controllers; it is often the
  case that you don't want to generate *all* graphs for *all* controllers, or
  that some graphs will crash because of missing data if you try to generate
  them with a specific controller.

Intra-Experiment Graphs
-----------------------

Configuration for each type of intra-experiment graph currently supported by
this plugin is below. Unless stated otherwise, all keys are required.

.. tabs::

   .. tab:: Stacked Linegraph

      The "stacked" here comes from multiple lines potentially being present
      (e.g., plotting all columns in a dataframe).

      .. literalinclude:: linegraph.yaml

   .. tab:: Heatmap

      .. literalinclude:: heatmap.yaml

Inter-Experiment Graphs
-----------------------

Configuration for each type of inter-experiment graph currently supported by
this plugin is below. Unless stated otherwise, all keys are required.

.. tabs::

   .. tab:: Stacked Linegraph

      The "stacked" here comes from multiple lines potentially being present
      (e.g., plotting the same column from the same file across all experiments
      in the batch).

      .. literalinclude:: linegraph.yaml

   .. tab:: Summary Linegraph

      The "summary" here comes from the selection of a single point from a time
      series of interest for each experiment in the batch. For example, if you
      took the *last* point of some measure of interest, that might summarize
      steady-state behavior.

      .. literalinclude:: linegraph.yaml

.. TODO:: Add inter-experiment heatmaps for bivariate criteria once support for
          it is put back into SIERRA.
