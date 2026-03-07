..
   Copyright 2025 John Harwell, All rights reserved.

   SPDX-License-Identifier:  MIT

.. _plugins/prod:

===========================
Product Generation (--prod)
===========================

These plugins run during stage 4, and therefore are dependent on certain stage 3
plugins having been run (each plugin calls out their dependencies). See
:ref:`concepts/dataflow/stage4` for information about how data flows/is
transformed during stage 4 processing.

With that context and framing, the documentation for each of the product
generation plugins which come with SIERRA are below.

.. toctree::
   :maxdepth: 1

   render.rst
   graphs.rst
