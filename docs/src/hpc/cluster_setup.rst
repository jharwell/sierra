.. _ln-hpc-cluster-setup:

=================
HPC Cluster Setup
=================

This setup applies to the following SIERRA HPC cluster environments:

- PBS: :ref:`ln-hpc-plugins-pbs`
- SLURM: :ref:`ln-hpc-plugins-slurm`

The steps to properly configure the C++ libraries for ARGoS and your project for
use with SIERRA in one of the above environments are:

#. Build ARGoS natively on each different type of compute node SIERRA might be
   run on, for maximum efficiency with large swarms. For example, if your HPC
   cluster is 1/2 Intel chips and 1/2 AMD chips, you will want to compile ARGoS
   twice, natively on each chipset, and link the architecture-dependent ARGoS
   into your ``PATH`` via ``argos3-<arch>``, where ``<arch>`` is anything you
   like; :envvar:`SIERRA_ARCH` will need to be set to ``<arch>`` before
   invocating SIERRA so that the correct ARGoS commands can be generated,
   depending on what the chipset is for the nodes you request for your HPC job.

#. Your project ``.so`` should be built natively on each different type of
   compute node SIERRA might be run on, just like ARGOS, for maximum efficiency
   with large swarms. Since the name of the ``.so`` is deduced from
   ``--project`` for SIERRA, you can use :envvar:`ARGOS_PLUGIN_PATH` to specify
   where the library should be loaded from (e.g., using :envvar:`SIERRA_ARCH` as
   the switch).

Once ARGoS/your C++ code has been built, you can setup SIERRA:

#. Install python dependencies with ``pip3``::

     pip3 install --user --upgrade pip
     pip3 install --user -r requirements/common.txt

#. Verify GNU :program:`parallel` is installed; if it is not installed, ask your
   cluster admin to install it for you.

#. Clone plugin for whatever project you are going to use into
   ``projects``. SIERRA will (probably) refuse to do anything useful if there are
   no project installed. The repository should be cloned into a directory with
   the EXACT name you want it to be callable with on the cmdline via
   ``--project``.

#. Read the documentation for :doc:`HPC plugins <plugins>`, and select and
   appropriate plugin to use. Be sure to define all necessary environment
   variables!!

.. WARNING:: Before invoking SIERRA in a cluster environment, you must ``cd`` to
   the directory where it is cloned; this is a limitation which will be removed
   in the future once SIERRA is a pypi package.
