..
   Copyright 2025 John Harwell, All rights reserved.

   SPDX-License-Identifier:  MIT

.. _plugins/compare:

==============================
Product Comparison (--compare)
==============================

SIERRA supports a number of comparator plugins, all of which can be used to
compare products/deliverables generated in stage 4 in some way.

Before reading this page, take a look at :ref:`concepts/exp-design`,
which details how SIERRA experiments are architected at a high-level; these
plugins tie in heavily to that architecture. Specifically, see :ref:`here
<concepts/dataflow/stage5>` for information about how output data flows/is
transformed during stage5 processing.

.. toctree::
   :maxdepth: 1

   graphs
