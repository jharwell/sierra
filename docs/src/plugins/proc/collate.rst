..
   Copyright 2025 John Harwell, All rights reserved.

   SPDX-License-Identifier:  MIT

.. _plugins/proc/collate:

===============================
Intra-Experiment Data Collation
===============================

Motivation
==========

When generating products, it is often necessary to perform some sort of
non-statistical mathematical analysis on the results. These calculations
*cannot* be done on the intra-experiment :term:`Processed Output Data` files,
because any calculated statistical distributions from them will be invalid; this
can be thought of as an average of sums is not the same as a sum of averages.
To support such use cases, SIERRA can make the necessary parts of the per-run
:term:`Raw Output Data` files available in stage 3 for doing such calculations
via :term:`Data Collation`. Of course, like all things in SIERRA, if you don't
need this functionality, you can turn it off by deselecting the plugin.

This process in stage 3 can be visualized as follows for a single
:term:`Experiment`, using :term:`Experimental Run` as SCOPE:

.. figure:: /figures/data-collation.png

Here, the user has specified that the ``col{0,1}`` in ``file0`` produced by all
experimental runs should be combined into a single file. Thus the
:term:`Collated Output Data` file generated from that specification will have
:math:`j` columns, one per run. Similarly for ``col{A,B}`` in ``file1``. This is
collation *within* in an experiment (intra-experiment). Collation *across*
experiments (if enabled/configured) is done during stage 4, and is handled by a
different plugin.

This plugin requires that the selected :ref:`storage plugin <plugins/storage>`
supports ``pd.DataFrame`` objects.

Usage
=====

This plugin can be selected by adding ``proc.collate`` to the list passed to
``--proc``.  Configuration for this plugin consists of *what* data to collate,
and some tweaks for *how* that data should be collated. When active, it will
create ``<batchroot>/statistics`` and the following directory structure::

  |-- <batchroot>
      |-- statistics
          |-- inter-exp


``inter-exp/`` contains :term:`Collated Output Data` files, drawn from specific
columns in :term:`Raw Output Data` files. This plugin outputs its data as
described above is so it can be used with :ref:`plugins/prod/graphs`, which
expects its outputs to be under ``statistics/``.

This plugin does not require additional plugins to be active when it is run.

Cmdline Interface
-----------------

.. argparse::
   :filename: ../sierra/plugins/proc/collate/cmdline.py
   :func: sphinx_cmdline_multistage
   :prog: sierra-cli

Configuration
-------------

Controls *what* to collate. Collated data is usually "interesting" in some way;
e.g., related to system performance. Configuration lives in a ``collate.yaml``
file; all fields are required unless otherwise specified.

.. code-block:: YAML

   # Contains a list of config items for intra-experiment collation (i.e.,
   # collation at the level of experimental runs).
   intra-exp:

     # Each config item has 'file' and 'cols' fields. 'file' specifies a
     # filepath, relative to the output directory for each experimental run,
     # containing the data columns of interest. 'cols' specifies the columns of
     # interest.
     - file: foo/bar
       cols:
         - col1
         - col2
