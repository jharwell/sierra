..
   Copyright 2025 John Harwell, All rights reserved.

   SPDX-License-Identifier:  MIT

.. _exp/stage5-dataflow:

============================
Stage 5 Inter-Batch Dataflow
============================

After :ref:`exp/stage4-dataflow`, data is in :term:`Processed Output Data` files
and/or :term:`Collated Output Data` files. In stage 5, the :term:`Collated
Output Data` files can be taken and further collated to create
:term:`Inter-Batch Data` files. The dataflow for this can be visualized as
follows, with :term:`Batch Experiment` as SCOPE.

.. figure:: /figures/data-collation.png

   Each output file is a summary of a set of batch experiments along some axis
   of interest.
