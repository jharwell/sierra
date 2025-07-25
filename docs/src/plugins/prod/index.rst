..
   Copyright 2025 John Harwell, All rights reserved.

   SPDX-License-Identifier:  MIT

.. _plugins/prod:

==========================
Product Generation Plugins
==========================

These plugins run during stage 4, and therefore are dependent on certain stage 3
plugins having been run (each plugin calls out their dependencies).

.. include:: /src/exp/stage4-dataflow.rst

Plugins
=======

With that context and framing, the documentation for each of the product
generation plugins which come with SIERRA are below.

.. toctree::

   render.rst
   graphs.rst
