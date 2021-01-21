Setup
=====

This page contains links to guides for setting up SIERRA in different HPC
environments from a C++ library point of view. To setup the SIERRA python plugin
for your project (specified on the cmdline via ``--project``, see
:ref:`ln-contrib-project`).

The general steps to integrate your project with SIERRA and a chosen HPC
environment are:

#. Figure out which HPC environment SIERRA supports matches your available
   hardware: :ref:`ln-hpc-plugins`.

#. If you have chosen the PBS or SLURM HPC environments, you will need to follow
   :ref:`ln-hpc-cluster-setup`. If you have chosen the local or adhoc environments,
   you will need to follow :ref:`ln-hpc-local-setup`.

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   hpc_plugins.rst
   hpc_local_setup.rst
   hpc_cluster_setup.rst
   msi_setup.rst
