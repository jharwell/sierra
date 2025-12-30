.. _plugins/execenv:

=============================
Execution Environment Plugins
=============================

High Performance Computing (HPC) Plugins
========================================

SIERRA is capable of adapting its runtime infrastructure to a number of
different HPC environments so that experiments can be run efficiently on
whatever computational resources a researcher has access to.  SIERRA makes the
following assumptions about the HPC environments corresponding to the plugins
listed on this page:

.. -table:: HPC Environment Assumptions
   :header-rows: 1

   * - Assumption

     - Rationale

   * - All nodes allocated to SIERRA have the same # of cores (can be less than
       the total # available on each compute node). Note that this may be *less*
       than the actual number of cores available on each node, if the HPC
       environment allows node sharing, and the job SIERRA runs in is allocated
       less than the total # cores on a given node.

     - Simplicity: If allocated nodes had different core counts, SIERRA would
       have to do more of the work of an HPC scheduler, and match jobs to
       nodes. May be an avenue for future improvement.

   * - All nodes have a shared filesystem.

     - Standard feature on HPC environments. If for some reason this is not
       true, stage 2 outputs will have to be manually placed such that it is as
       if everything ran on a common filesystem prior to running any later
       stages.


You may want to built e.g., ARGoS natively for your HPC cluster for maximum
efficiency; if your HPC cluster is 1/2 Intel chips and 1/2 AMD chips, you may
want to compile your :term:`Engine` twice, natively on each chipset. If you do
this, you can set :envvar:`SIERRA_ARCH` prior to invoking SIERRA so that the
correct invocation commands can be generated, depending on what the chipset is
for the nodes you request for your HPC job.  Similarly, you may want to build
your :term:`Project` ``.so`` (if your project is C/C++) natively on each
different type of compute node SIERRA might be run on, for maximum efficiency.

.. toctree::
   :maxdepth: 1

   hpc/local.rst
   hpc/adhoc.rst
   hpc/pbs.rst
   hpc/slurm.rst
   hpc/awsbatch.rst

Prefect-based Plugins
=====================

SIERRA is capable of adapting its runtime infrastructure to use :term:`Prefect`
flows so that experiments can be submitted to configured prefect servers, or run
locally. The names of prefect plugins begin with ``prefectserver`` instead of
``prefect`` to avoid ``sys.path`` conflicts with the ``prefect`` package which
will otherwise arise.

.. toctree::
   :maxdepth: 1

   prefectserver/local.rst
   prefectserver/dockerremote.rst

Real Robot Plugins
==================

SIERRA is capable of adapting its runtime infrastructure to a number of
different robots.

.. toctree::
   :maxdepth: 1

   realrobot/turtlebot3.rst

Additional execution environments can be supported via
:ref:`tutorials/plugin/execenv`.
