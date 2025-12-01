..
   Copyright 2025 John Harwell, All rights reserved.

   SPDX-License-Identifier:  MIT

.. _plugins/proc/pseudostats:

=================
Pseudo-Statistics
=================

When doing deterministic :term:`Experimental Runs <Experimental Run>`, there is
no benefit to running :ref:`plugins/proc/statistics` over the all experimental
run data for an :term:`Experiment`, because ``--n-runs=1``. Thus, the
statistical analysis via e.g., confidence intervals doesn't make sense.  This
plugin processes at the file level for each :term:`Experimental Run`. All
:term:`Raw Output Data` files produced by each run are copied (or moved)from
their original locations and written to the :ref:`usage/run-time-tree` under
``statistics/``. This is so it can be used with :ref:`plugins/prod/graphs`,
which expects its outputs to be under that prefix.

.. NOTE:: This plugin is not intended for use with projects whose output is
          non-deterministic (i.e., contain randomness). That is, if you always
          use ``--n-runs=>1`` , then you should consider using
          :ref:`plugins/proc/statistics` instead of this plugin.

Usage
=====

This plugin can be selected by adding ``proc.dataop`` to the list passed to
``--proc``. When active it will create ``<batchroot>/statistics``, and each
experiment will get their own directory in this root for their
statistics. E.g.::

  |-- <batchroot>
      |-- statistics
          |-- c1-exp0
          |-- c1-exp1
          |-- c1-exp2
          |-- c1-exp3

All experimental outputs are copied which are supported by the currently active
:ref:`storage plugin <plugins/storage>`.

Cmdline Interface
-----------------

.. argparse::
   :filename: ../sierra/plugins/proc/pseudostats/cmdline.py
   :func: sphinx_cmdline_multistage
   :prog: sierra-cli

.. WARNING:: If you use ``--dataop=move``, all of your experimental data will
             be moved from its original output directories to
             ``<batchroot>/statistics``! This will break stage 3 idempotency.

Configuration
-------------

None for the moment.
