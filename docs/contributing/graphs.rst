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

To add a linegraph, simply add a new entry to the
``projects/<project>/config/*.yaml`` file that will be
parsed by SIERRA in an appropriate category. Linegraphs are appropriate if:

- The data you want to graph can be represented by a line (i.e. is one
  dimensional in some way).

- The data you want to graph can be obtained from a single .csv file (multiple
  columns in the same .csv file can be graphed simultaneously).

Heatmaps
--------

To add a heatmap, simply add a new entry to the
``projects/<project>/config/*.yaml`` file that will be parsed by SIERRA in an
appropriate category. Heatmaps are appropriate if:

- The data you want to graph is two dimensional (e.g. a spatial representation
  of the arena is some way).

How to Add A New Inter-Experiment Graph
========================================

To add an inter-experiment graph, add an entry in the list of linegraphs found
in ``project/<project>/config/inter-exp-linegraphs.yaml`` in an appropriate
category. Inter-experiment linegraphs are appropriate if:

- The data you want to graph can be represented by a line (i.e. is one
  dimensional in some way).

- The data you want to graph can be obtained from a single column from a single
  ``.csv`` file.

- The data you want to graph requires comparison between multiple experiments in
  a batch.
