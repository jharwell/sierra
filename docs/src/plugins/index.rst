.. _plugins:

======================
SIERRA Builtin Plugins
======================

This is the landing page for the builtin plugins which come with SIERRA. SIERRA
currently supports:

- Multiple :term:`Platforms <Platform>` which researchers can write code to
  target.

- :ref:`Multiple execution environments <plugins/exec-env>`, for execution of
  experiments. Built-in support includes HPC environments and real hardware such
  as robots.

- :ref:`Multiple formats <plugins/expdef>` for experimental
  inputs, which are used to generating experiments, and :ref:`multiple formats
  <plugins/storage>` for experimental outputs.

- Processing of :term:`Raw Output Data` files in arbitrary ways via
  :ref:`processing plugins <plugins/proc>`. The dataflow for each of these
  plugins may be vastly different; refer to individual processing plugins for
  details on requirements, inputs/outputs, etc.

.. toctree::
   :maxdepth: 1
   :caption:

   platform/index.rst
   exec-env/index.rst
   storage/index.rst
   expdef/index.rst
   proc/index.rst
