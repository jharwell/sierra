..
   Copyright 2025 John Harwell, All rights reserved.

   SPDX-License-Identifier:  MIT

.. _plugins/proc/decompress:

==================
Data Decompression
==================

When dealing with :term:`Projects <Project>` which produce huge amounts of data,
it is easy to blow out allocated storage with uncompressed data if you run lots
of :term:`Batch Experiments <Batch Experiment>`. Thus, data for such projects is
often compressed after being written (by the :term:`Engine`, :term:`Project`, or
some other source). Before it can be processed, data for a given batch
experiment needs to be decompressed; that's where this plugin comes in.

This plugin processes at the file level for each :term:`Experimental Run`. All
matching archive types are decompressed. Currently supports:

- ``.tar.gz``

Usage
=====

This plugin can be selected by adding ``proc.decompress`` to the list passed to
``--proc``.
