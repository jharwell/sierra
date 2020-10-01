How to Add A New Intra-Experiment Graph Category
================================================

If you add a new intra-experiment graph category, it will not automatically be
used to generate graphs for existing or new controllers. You will need to modify
the ``controllers.yaml`` file to specify which controllers your new category of
graphs should be generated for.

How to Add A New Intra-Experiment Graph
=======================================

There are two types of intra-experiment graphs: linegraphs and heatmaps, and
each has their own config file (details of each is below).

**TEST YOUR NEW GRAPH TO VERIFY IT DOES NOT CRASH**. If it does, that likely
means that the .csv file the graph is build from is not being generated properly.

Linegraphs
----------

Each linegraph has the following YAML fields, which are parsed into a python
dictionary:

- ``src_stem`` - The filename (no path) of the .csv within the simulation output
  directory for a simulation, sans the .csv extension.

- ``dest_stem`` - The filename (no path) of the graph to be generated
  (extension/image type is determined elsewhere).

- ``cols``: List of names of columns within the source .csv that should be
  included on the plot. Must match EXACTLY (i.e. no fuzzy matching). Can be
  'None'/omitted to plot all columns within the .csv.

- ``styles`` - List of matplotlib linestyles to use for each of the plotted
  lines in the graphs. Can be omitted to use solid lines everywhere. If it is
  included, then it must specify for ALL columns, not just the non-default ones.

- ``title`` - The title the graph should have. LaTeX syntax is supported (uses
  matplotlib after all).

- ``legend`` - List of names of the plotted lines within the graph. Can be
  ``None``/omitted to set the legend for each column to the name of the column
  in the .csv

- ``xlabel`` - The label of the X-axis of the graph.

- ``ylabel`` - The label of the Y-axis of the graph.

To add a linegraph, simply add a new entry to the config file that will be
parsed by SIERRA in an appropriate category. Linegraphs are appropriate if:

- The data you want to graph can be represented by a line (i.e. is one
  dimensional in some way).

- The data you want to graph can be obtained from a single .csv file (multiple
  columns in the same .csv file can be graphed simultaneously).

Heatmaps
--------

Each linegraph has the following YAML fields, which are parsed into a python
dictionary:

- ``src_stem`` - The filename (no path) of the .csv within the output directory
  for a simulation to look for the column(s) to plot, sans the .csv extension.

- ``title`` - The title the graph should have. LaTeX syntax is supported (uses
  matplotlib after all).

To add a heatmap, simply add a new entry to the config file that will be
parsed by SIERRA in an appropriate category. Heatmaps are appropriate if:

- The data you want to graph is two dimensional (i.e. a spatial representation
  of the arena is some way).

How to Add A New Inter-Experiment Graph
========================================

Add an entry in the list of linegraphs found in ``inter-exp-linegraphs.yaml`` in
the ``config/`` directory in an appropriate category if:

- The data you want to graph can be represented by a line (i.e. is one
  dimensional in some way).

- The data you want to graph can be obtained from a single column from a single
  ``.csv`` file.

- The data you want to graph requires comparison between multiple experiments in
  a batch.
