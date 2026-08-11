.. _plugins/prod/graphs:

================
Graph Generation
================

This plugin generates graphs using holoviews during stage 4; any graph type
supported by a holoviews backend can be selected with
:ref:`--graphs-backend<src/plugins/prod/graphs:sierra---graphs-backend>`.
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

.. _plugins/prod/graphs/packages:

OS Packages
===========

.. tab-set::

   .. tab-item:: Ubuntu

      .. code-block:: bash

          apt-get install \
                  cm-super \
                  texlive-fonts-recommended \
                  texlive-latex-extra \
                  dvipng


   .. tab-item:: OSX

      .. code-block:: bash

         brew install --cask mactex-no-gui

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

Within each of these logical graph types, any
:ref:`--graphs-backend<src/plugins/prod/graphs:sierra---graphs-backend>` can
be specified to generate the actual graphs; overrideable on a per-graph
basis. This makes generating mixed e.g. static graphs for inclusion in
presentations and interactive graphs for inclusion in webpages easy.

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

   * - Histogram
     -

       - You want to see the *distribution* of one or more measures, rather
         than their evolution over time.

       - The columns you want to compare are commensurate enough to share a
         set of bins (they are binned over a shared range so that the
         distributions line up).

     - The data is contained in one or more columns in a single file. Each
       column contains numerical data.

   * - Scatterplot

     -

       - The data you want to graph is a set of (x, y) point pairs, and you want
         to see how one measure relates to another (correlation, trend) rather
         than either one's evolution over time.

       - You optionally want a line/curve of best fit (linear, polynomial, log,
         etc.) overlaid, with an R\ :sup:`2` goodness-of-fit value.

     - The data is contained in two columns in a single file: an X column and a
       Y column. The two columns must be the same length (each row is one
       point). Unlike time series, the points need not be ordered.

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
          |-- inter-exp

``inter-exp/`` contains graphs which are generated across experiments in the
batch from :term:`Batch Summary Data` files.

This plugin requires one of the following stage 3 plugins to have been run:

- :ref:`plugins/proc/statistics` (linegraphs, histograms). Without this, no
  statistics can be included.

- :ref:`plugins/proc/pseudostats`

Cmdline Interface
=================

.. sphinx_argparse_cli::
   :module: sierra.plugins.prod.graphs.cmdline
   :func: sphinx_cmdline_multistage
   :prog: sierra

Configuration
=============

This plugin is mostly configured via a ``graphs.yaml`` in the :term:`Project`
config root. The file is structured as follows:

.. versionchanged:: 1.5.12
               The ``src_stem`` and ``dest_stem`` keys were renamed to ``src``
               and ``dest`` (a value may be a path into a subdirectory, so
               "stem" was misleading). This is a breaking change: existing
               ``graphs.yaml`` files must be updated, since unknown keys are
               rejected at load time.

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


.. IMPORTANT:: When using the ``matplotlib`` backend, SIERRA tells matplotlib to
               use LaTeX internally to generate graph labels, titles, etc., so
               the standard LaTeX character restrictions within strings apply to
               all fields (e.g., '#' is illegal but '\\#' is OK). This does not
               apply to the ``bokeh`` backend, which does not use LaTeX.

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

Common Keys
-----------

The following keys are accepted by *every* graph type, and docs are not repeated
in the per-type configuration below.

.. list-table::
   :header-rows: 1
   :widths: 15 15 70
   :align: left

   * - Key
     - Required?
     - Meaning

   * - ``src``
     - Yes
     - The path of the source data file, relative to the output directory for an
       :term:`Experimental Run` and without the file extension. It is a path, not
       a bare stem: it may name a file in a subdirectory. It is matched
       *exactly*, not as a substring: a bare name (``output1D``) resolves at the
       output root, and a file in a subdirectory must be named by its path
       (``subdir1/subdir2/output1D``). A value matching more than one file is an
       error.

   * - ``dest``
     - No
     - The path of the graph to be generated (relative to the graph output
       directory, without the extension -- the extension/image type is
       determined by the backend). This allows multiple graphs to be generated
       from the same data file by plotting different combinations of columns. If
       omitted, defaults to ``src``.

   * - ``type``
     - Yes
     - Which kind of graph to generate. Must be one of ``stacked_line``,
       ``summary_line``, ``heatmap``, ``confusion_matrix``, ``histogram``, or
       ``network``, and selects which of the per-type key sets below applies.

   * - ``title``
     - No
     - The title the graph should have. Defaults to ``''``.

   * - ``backend``
     - No
     - The backend used to render this particular graph. Defaults to
       :ref:`--graphs-backend<src/plugins/prod/graphs:sierra---graphs-backend>`,
       so individual graphs can opt out of the global choice.

.. NOTE:: Configuration is validated against these key sets when it is loaded,
          before any graph is generated. An error anywhere in ``graphs.yaml``
          is therefore reported up front, and all problems found are reported
          together rather than one run at a time.

Intra-Experiment Graphs
-----------------------

Configuration for each type of intra-experiment graph currently supported by
this plugin is below. Unless stated otherwise, all keys are required.

.. tab-set::

   .. tab-item:: Stacked Linegraph

      The "stacked" here comes from multiple lines potentially being present
      (e.g., plotting all columns in a dataframe).

      .. literalinclude:: stacked_line.yaml

   .. tab-item:: Heatmap

      .. literalinclude:: heatmap.yaml

   .. tab-item:: Network

      .. NOTE:: Network graphs read a ``.graphml`` file (``<src>.graphml``
                in the experiment's statistics directory) rather than a ``.csv``
                like every other graph type, so the file must have been produced
                by an earlier stage.

      .. literalinclude:: network.yaml


   .. tab-item:: Confusion Matrix

      .. literalinclude:: confusion_matrix.yaml

   .. tab-item:: Histogram

      .. literalinclude:: histogram.yaml

   .. tab-item:: Scatterplot

      A scatterplot of ``ycol`` versus ``xcol``, drawn from two columns of the
      source file. Optionally overlays a curve of best fit via ``show_best_fit``
      and ``best_fit_kind``.

      .. literalinclude:: scatterplot.yaml

      .. NOTE:: R\ :sup:`2` is reported for every ``best_fit_kind``, but it is a
         meaningful goodness-of-fit measure only for the polynomial kinds
         (``linear``\/``quadratic``\/``cubic``). For ``log`` and ``exp`` --
         which are fit in a transformed space -- treat R\ :sup:`2` as a rough
         indicator only. A very low R\ :sup:`2` on a ``linear`` fit usually
         means the relationship is not linear, not that the data is meaningless.


Inter-Experiment Graphs
-----------------------

Configuration for each type of inter-experiment graph currently supported by
this plugin is below. Unless stated otherwise, all keys are required.

.. NOTE:: Inter-experiment graphs collate a single ``src`` across
   experiments. There is deliberately no way to draw a graph's data from
   *multiple* source files here: by stage 4, any multi-file joining has already
   happened upstream in stage 3 (see :ref:`plugins/proc/collate`, which supports
   joining columns from several files into one collated output). A graph that
   needs data originally spread across files should point ``src`` at the
   stage-3 output that already joined them. This keeps every product sourced
   from a single file. For how this collation reshapes the data, see
   :ref:`concepts/dataflow/stage4` and the data-shape note below.

.. _plugins/prod/graphs/data-shapes:

Collated Data Shapes
^^^^^^^^^^^^^^^^^^^^^^

During :term:`Data Collation`, SIERRA reshapes the per-experiment source data
into one of two dataframe shapes in the collated output file. Which shape is
used is a property of the *kind of data*, not something you configure -- but
knowing which shape a graph type uses helps when inspecting collated CSVs or
debugging missing data.

.. list-table::
   :header-rows: 1
   :widths: 20 25 55
   :align: left

   * - Shape
     - Graph Types
     - Description

   * - Wide (columnar)
     - ``stacked_line``, ``summary_line``, ``histogram``
     - One column per experiment; the column name is the experiment name. This
       is the natural shape for aligned time-series data that projects already
       emit, so no reshaping of research output is required. Because every
       column in a single file must share a height, experiments with shorter
       series have their columns padded with *trailing nulls*.

   * - Long (rowwise)
     - ``heatmap``, ``scatterplot``
     - One row per datapoint, carrying the experiment identity in a column
       (``exp`` for scatterplots; ``x``/``y`` experiment-space indices for
       heatmaps). This is the natural shape for point sets, where each
       experiment contributes an independent number of points. No padding is
       needed: experiments simply contribute different numbers of rows.

.. IMPORTANT:: Missing data (an experiment that ran but produced an empty or
   unusable source for a graph) is always recorded as **null/absent**, never as
   a synthesized ``0`` or ``-1``. A null appears in the collated CSV as an empty
   field (``,,``), which is distinguishable downstream from a genuine
   measurement of zero. This matters because any statistic (mean, quartile,
   etc.) computed over the collated data would be silently corrupted by a
   fabricated zero.

.. IMPORTANT:: The wide (time-series) collation path assumes that all
   experiments in a batch share the same *starting* index/timepoint, so that
   padding a shorter series with trailing nulls aligns it correctly against the
   others. Series that start at different x-values would be silently misaligned
   by this bottom-padding. This assumption holds for the currently supported
   batch criteria.

.. tab-set::

   .. tab-item:: Stacked Linegraph

      The "stacked" here comes from multiple lines potentially being present
      (e.g., plotting the same column from the same file across all experiments
      in the batch).

      "Nice" X-axis labels are not currently implement for inter-experiment
      stacked line graphs.

      .. literalinclude:: stacked_line.yaml

   .. tab-item:: Summary Linegraph

      The "summary" here comes from the selection of a single point from a time
      series of interest for each experiment in the batch. For example, if you
      took the *last* point of some measure of interest, that might summarize
      steady-state behavior.

      .. literalinclude:: summary_line.yaml

   .. tab-item:: Heatmap

      A 2D heatmap of data, drawn from a specified per-experiment time series
      (e.g., if you took the *last* point of some measure of interest, that
      might summarize steady-state behavior).

      The ``xlabel`` and ``ylabel`` fields are drawn from the current bivariate
      batch criteria, along with the x/y ticks.

      .. literalinclude:: heatmap.yaml

   .. tab-item:: Histogram

      A set of histograms with various rendering options. Can render numerical
      or categorical data.

      .. IMPORTANT:: For inter-experiment histograms ``cols`` must name
                     *exactly one* column. That column is extracted from every
                     experiment in the batch during :term:`Data Collation`, so
                     the collated file has one column *per experiment*; all of
                     those columns are then plotted together. Naming more than
                     one column is an error.

                     For intra-experiment histograms ``cols`` may name any
                     number of columns, all of which are plotted.

      .. literalinclude:: histogram.yaml

   .. tab-item:: Scatterplot

      For inter-experiment scatterplots, the ``xcol`` and ``ycol`` columns are
      extracted from *every* experiment in the batch during :term:`Data
      Collation` and pooled into a single long-format frame (see
      :ref:`plugins/prod/graphs/data-shapes`). Each experiment contributes its
      own set of (x, y) points; experiments with different numbers of points are
      handled without padding. All pooled points are then plotted together, so a
      single scatterplot shows the (x, y) relationship across the whole batch.

      .. literalinclude:: scatterplot.yaml


.. NOTE:: If the batch criteria has dimension > 1, inter-experiment linegraphs
          and histograms are disabled/ignored currently. This will hopefully be
          fixed in a future version of SIERRA. (SIERRA#357).


Linegraph Examples
==================

For these examples, we will use the following SIERRA cmd and YAML configuration
from the :xref:`ARGoS sample project <SIERRA_SAMPLE_PROJECT>`.

.. tab-set::

   .. tab-item:: SIERRA cmd

      ::

         sierra \
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

   .. tab-item:: YAML config

      .. code-block:: YAML

         intra-exp:
           LN_default:
             - src: collected-data
               dest: robot-counts
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

             - src: collected-data
               dest: food-counts
               cols:
                 - collected_food
               title: 'Collected Food Counts'
               legend:
                 - ''

               xlabel: 'Time'
               ylabel: '\# Items'
               type: 'stacked_line'

             - src: collected-data
               dest: swarm-energy
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

.. tab-set::

   .. tab-item:: matplotlib

      .. list-table::
         :header-rows: 0

         * - .. figure:: figures/graphs/argos/intra-none/SLN-food-counts.png

           - .. figure:: figures/graphs/argos/intra-none/SLN-robot-counts.png

         * - .. figure:: figures/graphs/argos/intra-none/SLN-swarm-energy.png

           -

   .. tab-item:: bokeh

      .. raw:: html
         :file: figures/graphs/argos/intra-none/SLN-food-counts.html

      .. raw:: html
         :file: figures/graphs/argos/intra-none/SLN-robot-counts.html

      .. raw:: html
         :file: figures/graphs/argos/intra-none/SLN-swarm-energy.html




If we then want to plot 95% confidence intervals by doing
``--dist-stats=conf95``:

.. tab-set::

   .. tab-item:: matplotlib

      .. list-table::
         :header-rows: 0
         :widths: 50 50

         * - .. figure:: figures/graphs/argos/intra-conf95/SLN-food-counts.png

           - .. figure:: figures/graphs/argos/intra-conf95/SLN-robot-counts.png

         * - .. figure:: figures/graphs/argos/intra-conf95/SLN-swarm-energy.png

           -

   .. tab-item:: bokeh

       .. raw:: html
          :file: figures/graphs/argos/intra-conf95/SLN-food-counts.html

       .. raw:: html
          :file: figures/graphs/argos/intra-conf95/SLN-robot-counts.html

       .. raw:: html
          :file: figures/graphs/argos/intra-conf95/SLN-swarm-energy.html

Same idea for box-and-whisker plots via ``--dist-stats=bw`` (not shown). Now
suppose we want the walking/resting counts to appear on separate graphs. YAML
configuration becomes:

.. code-block:: YAML

   - src: collected-data
     dest: robot-counts
     cols:
       - walking
     title: 'Robot Counts'
     legend:
       - 'Walking'

   - src: collected-data
     dest: robot-counts
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

.. tab-set::

   .. tab-item:: matplotlib

      .. list-table::
         :header-rows: 0

         * - .. figure:: figures/graphs/argos/inter/SLN-swarm-energy.png


           - .. figure:: figures/graphs/argos/inter/SM-swarm-energy-summary.png

   .. tab-item:: bokeh

      .. raw:: html
         :file: figures/graphs/argos/inter/SLN-swarm-energy.html

      .. raw:: html
         :file: figures/graphs/argos/inter/SM-swarm-energy-summary.html


For the summary graph, the X-axis labels are populated based on the :term:`Batch
Criteria` used. Obviously, this is for a *single* batch experiment; summary
graphs for multiple batch experiments can be combined in stage 5. See
:ref:`plugins/compare/graphs` for info.

Confusion Matrix Examples
=========================

For these examples, we will use the following SIERRA cmd and YAML configuration
from the :xref:`YAMLSIM sample project <SIERRA_SAMPLE_PROJECT>`

.. tab-set::

   .. tab-item:: SIERRA cmd

      ::

         sierra \
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

   .. tab-item:: YAML config

      .. code-block:: YAML

         intra-exp:
           CM_default:
             - src: confusion-matrix
               dest: confusion-matrix
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

.. tab-set::

   .. tab-item:: matplotlib

      .. list-table::
         :header-rows: 0

         * - .. figure:: figures/graphs/yamlsim/intra/CM-confusion-matrix.png


   .. tab-item:: bokeh

      .. raw:: html
         :file: figures/graphs/yamlsim/intra/CM-confusion-matrix.html

Histogram Examples
==================

For these examples, we will use the following SIERRA cmd and YAML configuration
from the :xref:`YAMLSIM sample project <SIERRA_SAMPLE_PROJECT>`

.. tab-set::

   .. tab-item:: SIERRA cmd

      ::

         sierra \
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

   .. tab-item:: YAML config

      .. code-block:: YAML

         intra-exp:
           HG_default:
             - src: entropy-data
               dest: entropy-data
               type: "histogram"
               kind: "overlay"
               title: "Entropy comparison"
               cols:
                 - entropy0
                 - entropy1
                 - entropy2
               bins: 50

Using the above command and ``.yaml`` configuration capabilities we can generate
graphs easily with ``--graphs-backend=matplotlib``, OR interactive widgets with
``--graphs-backend=bokeh``. Different kinds of histograms can be generated with
the ``kind`` option.

.. tab-set::

   .. tab-item:: matplotlib

      .. list-table::
         :header-rows: 0

         * - .. figure:: figures/graphs/yamlsim/intra/HG-random-noise-overlay.png

             Histogram from one experiment.

         * - .. figure:: figures/graphs/yamlsim/inter/HG-random-noise-col1-overlay.png

             Overlay histogram across all experiments.

         * - .. figure:: figures/graphs/yamlsim/inter/HG-random-noise-col1-steps.png

             Step histogram across all experiments.

         * - .. figure:: figures/graphs/yamlsim/inter/HG-random-noise-col1-facet.png

             Facet histogram across all experiments.

   .. tab-item:: bokeh

      .. raw:: html
         :file: figures/graphs/yamlsim/intra/HG-random-noise-overlay.html

      .. raw:: html
         :file: figures/graphs/yamlsim/inter/HG-random-noise-col1-overlay.html

      .. raw:: html
         :file: figures/graphs/yamlsim/inter/HG-random-noise-col1-steps.html

      .. raw:: html
         :file: figures/graphs/yamlsim/inter/HG-random-noise-col1-facet.html

Scatterplot Examples
====================
For these examples, we will use the following SIERRA cmd and YAML configuration
from the :xref:`JSONSIM sample project <SIERRA_SAMPLE_PROJECT>`.

.. tab-set::

   .. tab-item:: SIERRA cmd

      ::

         sierra \
            --sierra-root=~/test \
            --controller=default.default \
            --engine=plugins.jsonsim \
            --project=projects.sample_jsonsim \
            --n-runs=4 \
            --expdef-template=~/git/sierra-sample-project/exp/jsonsim/template.json \
            --scenario=scenario1 \
            --expdef=expdef.json \
            --jsonsim-path=~/git/sierra-sample-project/plugins/jsonsim/jsonsim.py \
            --proc proc.statistics proc.collate \
            --controller=default.default \
            --batch-criteria max_speed.1.9.C5 \
            --pipeline 1 2 3 4

   .. tab-item:: YAML config

      .. code-block:: YAML

         intra-exp:
           SP_default:
             - src: subdir3/output1D
               dest: noise-vs-noise-fit
               type: "scatterplot"
               title: "Batch Accuracy vs V-Score"
               xcol: batch_accuracy_percent
               ycol: batch_vscore
               xlabel: "Batch Accuracy Percent"
               ylabel: "Batch V-Score"
               show_best_fit: true
               best_fit_kind: "linear"

A scatterplot of two columns from a single experiment's data, optionally with a
line of best fit. Generate static images with ``--graphs-backend=matplotlib`` or
interactive widgets with ``--graphs-backend=bokeh``:

.. tab-set::

   .. tab-item:: matplotlib

      .. list-table::
         :header-rows: 0
         :widths: 50 50

         * - .. figure:: figures/graphs/jsonsim/intra/SP-noise-vs-noise.png

           - .. figure:: figures/graphs/jsonsim/intra/SP-noise-vs-noise-fit.png

   .. tab-item:: bokeh

      .. raw:: html
         :file: figures/graphs/jsonsim/intra/SP-noise-vs-noise.html

      .. raw:: html
         :file: figures/graphs/jsonsim/intra/SP-noise-vs-noise-fit.html
