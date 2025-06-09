..
   Copyright 2025 John Harwell, All rights reserved.

   SPDX-License-Identifier:  MIT

.. _plugins/proc/stat:

=====================
Statistics Generation
=====================

When doing Monte Carlo simulations, or dealing with any sort of :term:`Engine`
or :term:`Project` which contains randomness, data analysis an the ensemble
level is required. This plugin supports such analysis by automatically computing
statistics to e.g., enable plotting 95% confidence intervals on graph
products in stage 4.


This plugin processes at the file level for each :term:`Experimental Run`. All
:term:`Raw Output Data` files produced by each run are gathered and statistics
calculated, and the results written out as described in the
:ref:`usage/run_time_tree`.

Usage
=====

This plugin can be selected by adding ``proc.statistics`` to the list passed to
``--proc``.


Configuration
=============

See :ref:`usage/cli` documentation for ``--dist-stats``.

This plugin reads ``graphs.yaml`` for intra- and inter-experiment graphs. If
either are present, then it *only* gathers and processing data for the selected
graphs. If ``graphs.yaml`` is missing or doesn't contain specs for those graph
types, then *all* output data files are gathered and processed. This can take a
looooonnngggg time, depending on the amount of data produced and the filesystem
speed.
