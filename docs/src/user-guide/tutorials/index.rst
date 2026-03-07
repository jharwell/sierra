.. _tutorials:

=====================================
Configuration and Extension Tutorials
=====================================

This page contains tutorials to setup and/or extend SIERRA according to your
needs.

.. _tutorials/project:

.. toctree::
   :maxdepth: 1
   :caption: Configuring SIERRA projects:

   project/project.rst
   project/config/index.rst
   project/generators.rst
   project/new-bc.rst
   project/hooks.rst

.. _tutorials/extension:

.. IMPORTANT:: When creating *any* type of plugin, including a :term:`Project`
               plugin, the name of the plugin must specified as ``X.Y`` on the
               cmdline. This is required for pipeline plugins, because the
               plugin name is used as part of the ``import`` name. Not strictly
               required for project plugins, but requiring it makes
               internal handling of all types of plugins much simpler.

.. toctree::
   :maxdepth: 1
   :caption: Extending SIERRA with new plugins:

   plugin/engine/index.rst
   plugin/execenv/index.rst
   plugin/storage/index.rst
   plugin/expdef/index.rst
   plugin/proc/index.rst
   plugin/prod/index.rst
   plugin/compare/index.rst
