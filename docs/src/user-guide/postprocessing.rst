..
   Copyright 2026 John Harwell, All rights reserved.

   SPDX-License-Identifier:  MIT

.. _user-guide/postprocessing:

=======================
Post-Processing Results
=======================

Stage 3 transforms :term:`Raw Output Data` files from completed experiments
into :term:`Processed Output Data` ready for graph generation in stage 4.
Processing is driven by the ``--proc`` plugin chain: one or more plugin names
passed in order, each executed sequentially. The default chain is
``proc.statistics proc.collate``. For what each built-in plugin does, see
:ref:`tutorials/plugins/proc`. For the data quality and resource options
that apply across all plugins, see :ref:`reference/cli`.

.. _user-guide/postprocessing/chain:

Composing the Chain
===================

Plugins are run in the order given, and order matters. The constraints between
the built-in plugins are documented in their respective pages:

- :ref:`plugins/proc/statistics/ordering`
- :ref:`plugins/proc/collate/ordering`
- :ref:`plugins/proc/compress/ordering`
- :ref:`plugins/proc/decompress/ordering`
- :ref:`plugins/proc/imagize/ordering`
- :ref:`plugins/proc/modelrunner/ordering`
- :ref:`plugins/proc/pseudostats/ordering`

Common compositions:

.. code-block:: bash

   # Default: statistics then collation
   sierra-cli ... --proc proc.statistics proc.collate

   # Add imagizing for later video rendering via prod.render
   sierra-cli ... --proc proc.statistics proc.collate proc.imagize

   # Compress raw outputs after processing to recover disk space
   sierra-cli ... --proc proc.statistics proc.collate proc.compress

   # Decompress, reprocess, recompress after fixing a stage 3 issue
   sierra-cli ... --proc proc.decompress proc.statistics proc.collate proc.compress
