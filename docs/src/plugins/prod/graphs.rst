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

.. IMPORTANT:: In order to support out-of-the-box declarative syntax, this
               plugin requires that all the necessary data to generate a given
               graph is present in the *same* file.

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
     - Data Requirements

   * - Linegraph

     -

       - The data you want to graph can be represented by a line (i.e. is one
         dimensional in some way). Time series are a graph example of this.

       - The data you want to graph can be obtained from a single .csv file
         (multiple columns in the same CSV file can be graphed simultaneously).

       - You need/want statistical distribution information to be shown on the
         graphs to help determine statistical significance.

       - The data you want to graph requires comparison between multiple
         experiments in a batch.

     - The data is contained in one or more columns in a single file. Each
       column contains numerical data forming a time series.

   * - Heatmap

     -

       - The data you want to graph is two dimensional (e.g. a spatial
         representation of a 2D space).

       - You don't need/aren't interested in statistics (statistically
         significant differences between cells in a heatmap cannot be determined
         just from the graph itself).

     - The data is contained in 3 columns a single file: an X coord column, a Y
       coord column, and a Z (value) column.

   * - Confusion Matrix
     - The data you want to graph is a set of predicted vs actual category
       labels.
     - The data is contains {truth, predicted} columns.

   * - Network
     - The data you want to graph is a network (graph) of some kind.
     - The data is contained in a single GraphML file.


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

This plugin requires one of the following stage 3 plugins to have been run:

- :ref:`plugins/proc/stat` (linegraphs). Without this, no statistics can be
  included.

- :ref:`plugins/proc/copy`

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
      (e.g., plotting all columns in a dataframe).

      .. literalinclude:: stacked_line.yaml

   .. tab:: Heatmap

      .. literalinclude:: heatmap.yaml

   .. tab:: Network

      .. NOTE:: This graph is only available when :ref:`imagizing
                <plugins/proc/imagize>`. This may change in a future version of
                SIERRA.

      .. literalinclude:: network.yaml


   .. tab:: Confusion Matrix

      .. literalinclude:: confusion_matrix.yaml


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

   .. tab:: Heatmap

      A 2D heatmap of data, drawn from a specified per-experiment time series
      (e.g., if you took the *last* point of some measure of interest, that
      might summarize steady-state behavior).

      The ``xlabel`` and ``ylabel`` fields are drawn from the current bivariate
      batch criteria, along with the x/y ticks.

      .. literalinclude:: heatmap.yaml


.. NOTE:: If the batch criteria has dimension > 1, inter-experiment linegraphs
          are disabled/ignored currently. This will hopefully be fixed in a
          future version of SIERRA. (SIERRA#357).


Linegraph Examples
==================

For these examples, we will use the following SIERRA cmd and YAML configuration
from the :xref:`ARGoS sample project <SIERRA_SAMPLE_PROJECT>`.

.. tabs::

   .. tab:: SIERRA cmd

      ::

         sierra-cli \
           --sierra-root=~/test \
           --controller=foraging.footbot_foraging \
           --engine=engine.argos \
           --project=projects.sample_argos \
           --exp-setup=exp_setup.T1000.K5 \
           --n-runs=4 \
           --physics-n-engines=1 \
           --expdef-template=~/git/sierra-sample-project/exp/argos/template.argos \
           --scenario=LowBlockCount.10x10x2 \
           --with-robot-leds \
           --with-robot-rab \
           --controller=foraging.footbot_foraging \
           --batch-criteria population_size.Linear5.C5 \
           --exp-n-datapoints-factor=0.1 \
           --dist-stats=none

   .. tab:: YAML config

      .. code-block:: YAML

         intra-exp:
           - src_stem: collected-data
             dest_stem: robot-counts
             cols:
               - walking
               - resting
             title: 'Robot Counts'
             legend:
               - 'Walking'
               - 'Resting'

             xlabel: 'Time'
             ylabel: '\# Robots'
             type: 'stacked_line'

           - src_stem: collected-data
             dest_stem: food-counts
             cols:
               - collected_food
             title: 'Collected Food Counts'
             legend:
               - ''

             xlabel: 'Time'
             ylabel: '\# Items'
             type: 'stacked_line'

           - src_stem: collected-data
             dest_stem: swarm-energy
             cols:
               - energy
             title: 'Swarm Energy Over Time'
             legend:
               - ''

             xlabel: 'Time'
             type: 'stacked_line'

Intra-Experiment
----------------

As mentioned earlier, intra-experiment products are time-series based and
generated from processed data *within* each experiment. Using the above command
and ``.yaml`` configuration capabilities we can generate graphs easily with
``--graphs-backend=matplotlib``, OR interactive widgets with
``--graphs-backend=bokeh``:

.. tabs::

   .. tab:: matplotlib

      .. list-table::
         :header-rows: 0

         * - .. figure:: figures/graphs-intra-none-SLN-food-counts.png

           - .. figure:: figures/graphs-intra-none-SLN-robot-counts.png

         * - .. figure:: figures/graphs-intra-none-SLN-swarm-energy.png

           -

 .. tab:: bokeh

    .. raw:: html
       :file: figures/graphs-intra-none-SLN-food-counts.html

    .. raw:: html
       :file: figures/graphs-intra-none-SLN-robot-counts.html

    .. raw:: html
       :file: figures/graphs-intra-none-SLN-swarm-energy.html




If we then want to plot 95% confidence intervals by doing
``--dist-stats=conf95``:

.. tabs::

   .. tab:: matplotlib

      .. list-table::
         :header-rows: 0
         :widths: 50 50

         * - .. figure:: figures/graphs-intra-conf95-SLN-food-counts.png

           - .. figure:: figures/graphs-intra-conf95-SLN-robot-counts.png

         * - .. figure:: figures/graphs-intra-conf95-SLN-swarm-energy.png

           -

   .. tab:: bokeh

       .. raw:: html
          :file: figures/graphs-intra-conf95-SLN-food-counts.html

       .. raw:: html
          :file: figures/graphs-intra-conf95-SLN-robot-counts.html

       .. raw:: html
          :file: figures/graphs-intra-conf95-SLN-swarm-energy.html

Same idea for box-and-whisker plots via ``--dist-stats=bw`` (not shown). Now
suppose we want the walking/resting counts to appear on separate graphs. YAML
configuration becomes:

.. code-block:: YAML

   - src_stem: collected-data
     dest_stem: robot-counts
     cols:
       - walking
     title: 'Robot Counts'
     legend:
       - 'Walking'

   - src_stem: collected-data
     dest_stem: robot-counts
     cols:
       - resting
     title: 'Robot Counts'
     legend:
       - 'Resting'

It's really that easy!

Inter-Experiment
----------------

After stage 3, some data is in :term:`Processed Output Data` files. In stage 4,
we can run :term:`Data Collation` on either of these types of files in order to
further refine their contents but at the level of a experiments within a batch
rather than experimental runs within an experiment.  After collation,
inter-experiment products can be generated directly. These products can be
time-based, showing results from each experiment. Compare the two graphs, each
representing the same data: a measurement of swarm energy over time. The graph
on the right is arguably more readable because it summarizes the steady-state
information more clearly.

.. tabs::

   .. tab:: matplotlib

      .. list-table::
         :header-rows: 0

         * - .. figure:: figures/graphs-inter-SLN-swarm-energy.png


           - .. figure:: figures/graphs-inter-SM-swarm-energy.png

   .. tab:: bokeh

      .. raw:: html
         :file: figures/graphs-inter-SLN-swarm-energy.html

      .. raw:: html
         :file: figures/graphs-inter-SM-swarm-energy.html


For the summary graph, the X-axis labels are populated based on the :term:`Batch
Criteria` used. Obviously, this is for a *single* batch experiment; summary
graphs for multiple batch experiments can be combined in stage 5. See
:ref:`plugins/compare/graphs` for info.

Confusion Matrix Examples
=========================

For these examples, we will use the following SIERRA cmd and YAML configuration
from the :xref:`YAMLSIM sample project <SIERRA_SAMPLE_PROJECT>`

.. tabs::

   .. tab:: SIERRA cmd

      ::

         sierra-cli \
            --sierra-root=~/test \
            --controller=default.default \
            --engine=plugins.yamlsim \
            --project=projects.sample_yamlsim \
            --n-runs=4 \
            --expdef-template=~/git/sierra-sample-project/exp/yamlsim/template.yaml \
            --scenario=scenario1 \
            --expdef=expdef.yaml \
            --yamlsim-path=~/git/sierra-sample-project/plugins/yamlsim/yamlsim.py \
            --proc proc.statistics proc.collate \
            --controller=default.default \
            --batch-criteria noise_floor.1.9.C5 \
            --pipeline 1 2 3 4

   .. tab:: YAML config

      .. code-block:: YAML

         intra-exp:
           CM_default:
             - src_stem: confusion-matrix
               dest_stem: confusion-matrix
               type: "confusion_matrix"
               title: "I'm A Little Confused"
               truth_col: Actual_Class
               predicted_col: Predicted_Class

Intra-Experiment
----------------

In addition to time-series based outputs, projects can also output
classification data in terms of predicted vs actual labels. These can be
combined into confusion matrices within each experiment to give a nice summary
of performance. Using the above command and ``.yaml`` configuration capabilities
we can generate graphs easily with ``--graphs-backend=matplotlib``, OR
interactive widgets with ``--graphs-backend=bokeh``:

.. tabs::

   .. tab:: matplotlib

      .. list-table::
         :header-rows: 0

         * - .. figure:: figures/graphs-intra-CM-confusion-matrix.png


   .. tab:: bokeh

      .. raw:: html
         :file: figures/graphs-intra-CM-confusion-matrix.html
