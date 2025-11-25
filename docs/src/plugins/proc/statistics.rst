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
:ref:`usage/run-time-tree`.

This plugin requires that the selected :ref:`storage plugin <plugins/storage>`
supports ``pd.DataFrame`` objects.

Usage
=====

This plugin can be selected by adding ``proc.statistics`` to the list passed to
``--proc``. When active it will create ``<batchroot>/statistics``, and all
statistics generated during stage 3 will accrue under this root directory. Each
experiment will get their own directory in this root for their
statistics. E.g.::

  |-- <batchroot>
      |-- statistics
          |-- c1-exp0
          |-- c1-exp1
          |-- c1-exp2
          |-- c1-exp3
          |-- collated
          |-- exec


``inter-exp/`` contains :term:`Collated Output Data` files. During stage4,
SIERRA will draw specific columns from :term:`Raw Output Data` files under and
collate them under here for later processing. ``exec/`` contains statistics
about SIERRA runtime. Useful for capturing runtime of specific experiments to
better plan/schedule time on HPC clusters.

Cmdline Interface
-----------------

.. argparse::
   :filename: ../sierra/plugins/proc/statistics/cmdline.py
   :func: sphinx_cmdline_multistage
   :prog: sierra-cli

Configuration
-------------

This plugin reads ``graphs.yaml`` for intra- and inter-experiment graphs. If
either are present, then it *only* gathers and processing data for the selected
graphs. If ``graphs.yaml`` is missing or doesn't contain specs for those graph
types, then *all* output data files are gathered and processed. This can take a
looooonnngggg time, depending on the amount of data produced and the filesystem
speed.
