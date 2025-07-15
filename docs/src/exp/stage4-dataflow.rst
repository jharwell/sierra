..
   Copyright 2025 John Harwell, All rights reserved.

   SPDX-License-Identifier:  MIT

Stage 4 Dataflow
================

Intra-Experiment Products
-------------------------

After :ref:`dataflow/stage3/intra-proc`, data is in :term:`Processed Output
Data` files and/or :term:`Collated Output Data` files. In stage 4, the
:term:`Processed Output Data` files can be taken and directly converted to
intra-experiment products such as graphs and videos with appropriate
plugins.  Reminder: these files *cannot* be used as inputs into mathematical
calculations for statistical reasons; the :term:`Collated Output Data` files
should be used as into mathematical calculations if needed. Of course, like all
things in SIERRA, if you don't need thus functionality, you can turn it off by
deselecting the plugin.

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
-------------------------

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
