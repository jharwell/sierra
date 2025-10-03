.. _plugins/prod/graphs:

================
Graph Generation
================

This plugin generates graphs using holoviews during stage 4; any graph type
supported by a holoviews backend can be selected with ``--graphs-backend``.
Since this plugin uses holoviews to do all the heavy lifting, you may wonder
"Why wrap holoviews backends at all?" A wrapper of a wrapper would seem
gratuitous at first glance. The reason is that SIERRA's wrapping here enables
*declarative* generation graphs supported by any of the holoviews backends. If
you used holoviews directly, you would have to change your python code to use a
different backend, as well as to account for subtleties when switching between
backends which are not yet ironed out in holoviews. SIERRA's declarative
approach here enables you focus on your goal (what type of graph to generate,
what you want on it, etc.), rather than the details of *how* that is
implemented.

Intra-Experiment Products
=========================

As mentioned earlier, intra-experiment products are time-series based and
generated from processed data *within* each experiment. For example, here is a
very simple time-based graph generated from one of the sample projects
containing estimates of swarm energy over time for one experiment. Note the
confidence intervals automatically added by SIERRA (this can of course also be
turned off via cmdline).

.. figure:: /figures/dataflow-intra-graph-ex0.png
   :width: 300

.. IMPORTANT:: All configuration for the graph above was specified via YAML--no
               python coding needed!

Inter-Experiment Products
=========================

After :ref:`plugins/proc/dataflow`, data is in :term:`Collated Output Data`
files and/or :term:`Collated Output Data` files. In stage 4, we can run
:term:`Data Collation` on either of these types of files in order to further
refine their contents, following an analogous process as outlined above, but at
the level of a experiments within a batch rather than experimental runs within
an experiment. Of course, like all things in SIERRA, if you don't need thus
functionality, you can turn it off by deselecting the plugin.

After collation, inter-experiment products can be generated directly. These
products can be time-based, showing results from each experiment, like this:

.. figure:: /figures/dataflow-inter-graph-ex0.png
   :width: 300

This is a very messy graph because of the width of confidence intervals, but it
does illustrate SIERRA's ability to combine data across experiments in a batch.

Or they can be summary graphs instead, based on some sort of summary
measure. For example, an inter-experiment summary linegraph complement to the
one above would look like this:

.. figure:: /figures/dataflow-inter-graph-ex1.png
   :width: 300

The X-axis labels are populated based on the :term:`Batch Criteria`
used. Obviously, this is for a *single* batch experiment; summary graphs for
multiple batch experiments can be combined in stage 5.

.. IMPORTANT:: All configuration for the graphs above were specified via
               YAML--no python coding needed!

This plugin has the following stage 3 plugin recommendations:

- :ref:`plugins/proc/stat` (all graphs). Without this, no statistics can be
  included on graphs.

.. _plugins/prod/graphs/packages:

OS Packages
===========

.. tabs::

      .. group-tab:: Ubuntu

         Install the following required packages with ``apt install``:

         - ``cm-super``
         - ``texlive-fonts-recommended``
         - ``texlive-latex-extra``
         - ``dvipng``


      .. group-tab:: OSX

         Install the following required packages with ``brew install``:

         - ``--cask mactex-no-gui``

Usage
=====

This plugin can be selected by adding ``prod.graphs`` to the list passed to
``--prod``. This plugin supports two logical types of graphs, and therefore two
types of analyses:

- Intra-experiment graphs, which can be thought of as graphs generated directly
  from the aggregated data from a set of :term:`Experimental Runs <Experimental
  Run>`.

- Inter-experiment graphs, which are generated from a selected subset of data
  from each :term:`Experiment` in a :term:`Batch Experiment`.

Within each of these logical graph types, any ``--graphs-backend`` can be
specified to generate the actual graphs; overrideable on a per-graph basis. This
makes generating mixed e.g. static graphs for inclusion in presentations and
interactive graphs for inclusion in webpages easy.

.. list-table::
   :header-rows: 1
   :align: left

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

       - You don't need/aren't interested in statistics (statistically
         significant differences between cells in a heatmap cannot be determined
         just from the graph itself).

This plugin can be selected by adding ``prod.graphs`` to the list passed to
``--prod``. When active  will create ``<batchroot>/graphs``, and all
graphs generated during stage 4 will accrue under this root directory. Each
experiment will get their own directory in this root for their
statistics. E.g.::

  |-- <batchroot>
      |-- graphs
          |-- c1-exp0
          |-- c1-exp1
          |-- c1-exp2
          |-- c1-exp3
          |-- collated

``inter-exp/`` contains graphs which are generated across experiments in the
batch from :term:`Batch Summary Data` files.

Cmdline Interface
=================

.. argparse::
   :filename: ../sierra/plugins/prod/graphs/cmdline.py
   :func: sphinx_cmdline_multistage
   :prog: sierra-cli

Configuration
=============

This plugin is mostly configured via a ``graphs.yaml`` in the :term:`Project`
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
      (e.g., plotting all columns in a dataframe). This is a time series graph,
      with the X-axis labels being either dataframe indices or specified in a
      :term:`Engine` specific way; see :ref:`tutorials/plugin/engine/prod` for
      specifics of this hook.

      .. literalinclude:: stacked_line.yaml

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

      "Nice" X-axis labels are not currently implement for inter-experiment
      stacked line graphs.

      .. literalinclude:: stacked_line.yaml

   .. tab:: Summary Linegraph

      The "summary" here comes from the selection of a single point from a time
      series of interest for each experiment in the batch. For example, if you
      took the *last* point of some measure of interest, that might summarize
      steady-state behavior.

      .. literalinclude:: summary_line.yaml

   .. tab:: heatmap

      A 2D heatmap of data, drawn from a specified per-experiment time series
      (e.g., if you took the *last* point of some measure of interest, that
      might summarize steady-state behavior).

      .. literalinclude:: heatmap.yaml

.. NOTE:: If the batch criteria has dimension > 1, inter-experiment linegraphs
          are disabled/ignored currently. This will hopefully be fixed in a
          future version of SIERRA. (SIERRA#357).
