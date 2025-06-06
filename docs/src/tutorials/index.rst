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
   project/main-config/index.rst
   project/stage5-config.rst
   project/generators.rst
   project/new-bc.rst
   project/hooks.rst
   project/models.rst

.. _tutorials/hpc:

.. toctree::
   :maxdepth: 1
   :caption: Configuring HPC environments:

   hpc/cluster_setup.rst
   hpc/local_setup.rst

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
   plugin/exec-env/index.rst
   plugin/storage/index.rst
   plugin/expdef/index.rst

.. toctree::
   :maxdepth: 1
   :caption: Misc Tutorials

   misc/cmdline.rst
