.. _ln-sierra-tutorials-hpc-cluster-setup:

=================
HPC Cluster Setup
=================

These instructions assume you already have SIERRA working with your project on
your local machine. If you haven't done that yet--shoo!

This setup applies to the following SIERRA HPC cluster environments:

- :ref:`ln-sierra-hpc-plugins-pbs`
- :ref:`ln-sierra-hpc-plugins-slurm`

ARGoS Setup on HPC Clusters
===========================

The steps to properly configure the C++ libraries for :term:`ARGoS` and your
:term:`Project` for use with SIERRA in one of the above environments are:

#. Build ARGoS natively for your cluster for maximum efficiency.

   .. NOTE:: If your HPC cluster is 1/2 Intel chips and 1/2 AMD chips, you may
             want to compile ARGoS twice, natively on each chipset. If you do
             this, you can set :envvar:`SIERRA_ARCH` prior to invoking SIERRA so
             that the correct ARGoS commands can be generated, depending on what
             the chipset is for the nodes you request for your HPC job.

#. Your project ``.so`` should be built natively on each different type of
   compute node SIERRA might be run on, just like ARGOS, for maximum efficiency
   with large swarms. You can use :envvar:`ARGOS_PLUGIN_PATH` (which is not
   modified by SIERRA) to specify where the library should be loaded from (e.g.,
   using :envvar:`SIERRA_ARCH` as the switch in your script which invokes
   SIERRA).

Once ARGoS/your C++ code has been built, you can setup SIERRA:

#. Install SIERRA package by following the instructions in :ref:`ln-sierra-packages`.

#. Verify GNU :program:`parallel` is installed; if it is not installed, ask your
   cluster admin to install it for you.

#. Clone plugin for whatever project you are going to use somewhere on your
   :envvar:`SIERRA_PLUGIN_PATH`. SIERRA will refuse to do anything useful if
   there is no project selected. The repository should be cloned into a
   directory with the EXACT name you want it to be callable with on the cmdline
   via ``--project``.

#. Read the documentation for :ref:`ln-sierra-exec-env-hpc`, and select and
   appropriate plugin to use. Be sure to define all necessary environment
   variables!!

GazeboS Setup on HPC Clusters
=============================

TBD.
