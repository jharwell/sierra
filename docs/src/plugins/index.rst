.. _plugins:

==============
SIERRA Plugins
==============

This is the landing page for all things plugins in SIERRA. SIERRA currently
supports several different plugin types:

- Multiple :term:`Engines <Engine>` which researchers can write code to
  target.

- :ref:`Multiple execution environments <plugins/execenv>`, for execution of
  experiments. Built-in support includes HPC environments and real hardware such
  as robots.

- :ref:`Multiple formats <plugins/expdef>` for experimental
  inputs, which are used to generating experiments, and :ref:`multiple formats
  <plugins/storage>` for experimental outputs.

- Processing of :term:`Raw Output Data` files in arbitrary ways via
  :ref:`processing plugins <plugins/proc>`. The dataflow for each of these
  plugins may be vastly different; refer to individual processing plugins for
  details on requirements, inputs/outputs, etc.

- Generating :term:`Products <Product>`, such as graphs/videos, from
  :term:`Processed Output Data` files via :ref:`product plugins
  <plugins/prod>`. The dataflow for each of these
  plugins may be vastly different; refer to individual processing plugins for
  details on requirements, inputs/outputs, etc.

- Comparing generated products in some way via :ref:`comparison plugins
  <plugins/compare>`. This could mean combining multiple graphs into a single
  graph, for example.

To use any of the builtin in SIERRA you don't need to do anything but select
them when invoking SIERRA via the appropriate cmdline switch. Details on
configuration, capabilities, etc. is below for each category of plugins SIERRA
supports.

.. toctree::
   :maxdepth: 1

   engine/index.rst
   execenv/index.rst
   storage/index.rst
   expdef/index.rst
   proc/index.rst
   prod/index.rst
   compare/index.rst

Other Plugin Resources
======================

.. toctree::
   :maxdepth: 1

   devguide.rst
   external.rst
