..
   Copyright 2025 John Harwell, All rights reserved.

   SPDX-License-Identifier:  MIT

.. _plugins/proc/stat:

=====================
Statistics Generation
=====================

When doing Monte Carlo simulations, or dealing with any sort of :term:`Platform`
or :term:`Project` which contains randomness, data analysis an the ensemble
level is required. This plugin supports such analysis by automatically computing
statistics to e.g., enable plotting 95% confidence intervals on graph
deliverables in stage 4.


This plugin processes at the file level for each :term:`Experimental Run`. All
:term:`Raw Output Data` files produced by each run are gathered and statistics
calculated, and the results written out as described in the
:ref:`usage/run_time_tree`.

Configuration
=============

See :ref:`usage/cli` documentation for ``--dist-stats``.
