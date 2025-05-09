.. _tutorials/project/graphs-config:

===================
Graph Configuration
===================

This page has the following sections:

- How to create a new :term:`Graph Category`

- How to define a new graph within a :term:`Graph Category` to generate from
  :term:`Experimental Run` outputs.

- How to "activate" the new graph so that it will be generated from experimental
  run outputs where applicable.

- How to generate additional graphs during stage 4 beyond those possible with
  the SIERRA core.

Create A New Graph Category
===========================

First, add a dictionary to ``<project>/config/graphs.yaml``.  Graph category
names can start anything, but something sensible like ``LN_`` should be used for
e.g., linegraphs.  An example ``graphs.yaml``, defining two categories of
linegraphs, one for intra-experiment linegraphs, and one for inter-experiment
linegraphs.:

.. code-block:: YAML

    intra-exp:
       LN_mycategory1:
         graphs:
           - ...
           - ...
           - ...
     inter-exp:
       LN_mycategory2:
         graphs:
           - ...
           - ...
           - ...

.. IMPORTANT:: Because SIERRA tells uv -> matplotlib to use LaTeX internally to
               generate graph labels, titles, etc., the standard LaTeX character
               restrictions within strings apply to all fields (e.g., '#' is
               illegal but '\#' is OK).


Add A New Intra-Experiment Graph To An Existing Category
========================================================

There are two types of intra-experiment graphs: linegraphs and heatmaps, and
each has their own config file (details of each is below).

Linegraphs
----------

Linegraphs are appropriate if:

- The data you want to graph can be represented by a line (i.e. is one
  dimensional in some way).

- The data you want to graph can be obtained from a single .csv file (multiple
  columns in the same CSV file can be graphed simultaneously).

The config block for each linegraph is below. Unless stated otherwise, all keys
are mandatory.

.. code-block:: YAML

   LN_mycategory:
     # The filename (no path) of the CSV within the experimental run output
     # directory for an experimental run, sans the CSV extension.
     - src_stem: 'foo'

     # The filename (no path) of the graph to be generated
     # (extension/image type is determined elsewhere). This allows for multiple
     # graphs to be generated from the same CSV file by plotting different
     # combinations of columns.
     - dest_stem: 'bar'

     # List of names of columns within the source CSV that should be
     # included on the plot. Must match EXACTLY (i.e. no fuzzy matching). Can be
     # omitted to plot all columns within the CSV.
     - cols:
         - 'col1'
         - 'col2'
         - 'col3'
         - '...'

     # The title the graph should have. LaTeX syntax is supported (uses
     # matplotlib after all). Optional.
     - title: 'My Title'

     # The type of graph. Possible values are 'stacked_line', and
     # 'summary_line' (inter-experiment only).
     - graph_type: 'stacked_line'

     # List of names of the plotted lines within the graph. Can be
     # omitted to set the legend for each column to the name of the column
     # in the CSV.
     - legend:
         - 'Column 1'
         - 'Column 2'
         - 'Column 3'
         - '...'

     # The label of the X-axis of the graph. Optional.
     - xlabel: 'X'

     # The label of the Y-axis of the graph. Optional.
     - ylabel: 'Y'


Heatmaps
--------

Heatmaps are appropriate if:

- The data you want to graph is two dimensional (e.g. a spatial representation
  of the arena is some way).

The config block for heatmaps is below. Unless stated otherwise, all keys are
mandatory.

.. code-block:: YAML

   graphs:
     # The filename (no path) of the CSV within the output directory
     # for an experimental run to look for the column(s) to plot, sans the CSV
     # extension.
     - src_stem: 'fooCSV'

     # The title the graph should have. LaTeX syntax is supported (uses
     # matplotlib after all). Optional for  all heatmaps except those created
     # during imagizing.
     - title: 'My Title'

     # The type of graph. Must be 'heatmap'.
     - graph_type: 'heatmap'

     # The Z colorbar label to use. Optional.
     - zlabel: 'My colorbar label'

How to Add A New Inter-Experiment Graph
=======================================

Linegraphs
----------

Inter-experiment linegraphs are appropriate if:

- The data you want to graph can be represented by a line (i.e. is one
  dimensional in some way).

- The data you want to graph can be obtained from a single column from a single
  CSV file.

- The data you want to graph requires comparison between multiple experiments in
  a batch.

The config is the same as intra-experiment linegraphs, EXCEPT the ``graph_type``
field can now be "summary_line" to generate a
:func:`~sierra.core.graphs.summary_line`.

Heatmaps
--------

Inter-experiment heatmaps are appropriate if:

- You are using bivariate batch criteria.

- The data you want to graph can be represented by a line (i.e. is one
  dimensional in some way).

- The data you want to graph can be obtained from a single column from a single
  CSV file.

- The data you want to graph requires comparison between multiple experiments in
  a batch.

.. versionadded:: 1.2.20


The config block is the same as intra-experiment heatmaps.


How to Activate New Graph Category
==================================

If you added a new :term:`Graph Category`, it will not automatically be used to
generate graphs for existing or new controllers. You will need to modify the
``<project>/config/controllers.yaml`` file to specify which controllers your new
category of graphs should be generated for. See
:ref:`tutorials/project/main-config` for details.
