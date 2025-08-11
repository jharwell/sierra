..
   Copyright 2025 John Harwell, All rights reserved.

   SPDX-License-Identifier:  MIT

.. _plugins/proc/compress:

================
Data Compression
================

When dealing with :term:`Projects <Project>` which produce huge amounts of data,
it is easy to blow out allocated storage with uncompressed data if you run lots
of :term:`Batch Experiments <Batch Experiment>`. Thus, it is often useful to
compress data for such projects; that's where this plugin comes in.  Keep in
mind that this plugin runs during stage 3, so if you generate so much data
during stage 2 so as to blow out your disk, this plugin can't help.  However,
you can look at
:class:`~sierra.core.experiment.bindings.IExpRunShellCmdsGenerator` and add
whatever commands needed after each run to compress the data if you generate
ungodly amounts of data.

This plugin processes at the file level for each :term:`Experimental Run`. The
entire output tree is compressed to a ``.tar.gz`` file. Optionally, the
uncompressed data can be removed after compression with
``--compress-remove-after``. No data is lost--it's all in the archive!

Usage
=====

This plugin can be selected by adding ``proc.decompress`` to the list passed to
``--proc``.

Cmdline Interface
-----------------

.. argparse::
   :filename: ../sierra/plugins/proc/compress/cmdline.py
   :func: sphinx_cmdline_stage3
   :prog: sierra-cli
