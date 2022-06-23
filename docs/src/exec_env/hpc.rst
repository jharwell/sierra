.. _ln-sierra-exec-env-hpc:

==============================================================
High Performance Computing (HPC) Execution Environment Plugins
==============================================================

SIERRA is capable of adapting its runtime infrastructure to a number of
different HPC environments so that experiments can be run efficiently on
whatever computational resources a researcher has access to. Supported
environments that come with SIERRA are listed on this page.

These plugins tested with the following platforms (they may work on other
platforms out of the box too):

- :ref:`ln-sierra-platform-plugins-argos`
- :ref:`ln-sierra-platform-plugins-ros1gazebo`

.. _ln-sierra-hpc-plugins-local:

Local HPC Plugin
================

This HPC environment can be selected via ``--exec-env=hpc.local``.

This is the default HPC environment in which SIERRA will run all experiments on
the same computer from which it was launched using GNU parallel.  The #
simultaneous simulations will be determined by::

  # cores on machine / # threads per experimental run

If more simulations are requested than can be run in parallel, SIERRA will start
additional simulations as currently running simulations finish.

No additional configuration/environment variables are needed with this HPC
environment for use with SIERRA.

ARGoS Considerations
--------------------

The # threads per :term:`experimental run <Experimental Run>` is defined with
``--physics-n-engines``, and that option is required for this HPC environment
during stage 1.

.. _ln-sierra-hpc-plugins-pbs:

PBS HPC Plugin
==============

This HPC environment can be selected via ``--exec-env=hpc.pbs``.

In this HPC environment, SIERRA will run experiments spread across multiple
allocated nodes by a PBS compatible scheduler such as Moab. SIERRA makes the
following assumptions about the compute nodes it is allocated each invocation:

- All nodes have the same # of cores (can be less than the total # available on
  each compute node).

- All nodes have a shared filesystem.


The following table describes the PBS-SIERRA interface. Some PBS environment
variables are used by SIERRA to configure experiments during stage 1,2 (see
TOQUE-PBS docs for meaning); if they are not defined SIERRA will throw an error.

.. list-table:: PBS-SIERRA interface
   :widths: 25,50
   :header-rows: 1

   * - PBS environment variable

     - SIERRA context

   * - PBS_NUM_PPN

     - Used to calculate # threads per experimental run for each allocated
       compute node via::

         floor(PBS_NUM_PPN / --exec-jobs-per-node)

       That is, ``--exec-jobs-per-node`` is required for PBS HPC environments.

   * - PBS_NODEFILE

     - Obtaining the list of nodes allocated to a job which SIERRA can direct
       GNU parallel to use for experiments.

   * - PBS_JOBID

     - Creating the UUID nodelist file passed to GNU parallel, guaranteeing
       no collisions (i.e., simultaneous SIERRA invocations sharing allocated
       nodes) if multiple jobs are started from the same directory.

The following additional environmental variables must be defined appropriately
when using the PBS HPC environment; if they are not defined SIERRA will throw
an error.

- :envvar:`SIERRA_ARCH`

- :envvar:`PARALLEL`

.. _ln-sierra-hpc-plugins-slurm:

SLURM HPC Plugin
================

`<https://slurm.schedmd.com/documentation.html>`_

This HPC environment can be selected via ``--exec-env=hpc.slurm``.

In this HPC environment, SIERRA will run experiments spread across multiple
allocated nodes by the SLURM scheduler. SIERRA makes the following assumptions
about the compute nodes it is allocated each invocation:

- All nodes have the same # of cores (can be less than the total # available on
  each compute node).

- All nodes have a shared filesystem.

The following table describes the SLURM-SIERRA interface. Some SLURM environment
variables are used by SIERRA to configure experiments during stage 1,2 (see
SLURM docs for meaning); if they are not defined SIERRA will throw an error.

.. list-table:: SLURM-SIERRA interface
   :widths: 25,50
   :header-rows: 1

   * - SLURM environment variable

     - SIERRA context

   * - SLURM_CPUS_PER_TASK
     - Used to set # threads per experimental node for each allocated compute
       node.

   * - SLURM_TASKS_PER_NODE
     - Used to set # parallel jobs per allocated compute node. Overriden by
       ``--exec-jobs-per-node`` if passed.

   * - SLURM_JOB_NODELIST

     - Obtaining the list of nodes allocated to a job which SIERRA can direct
       GNU parallel to use for experiments.

   * - SLURM_JOB_ID

     - Creating the UUID nodelist file passed to GNU parallel, guaranteeing no
       collisions (i.e., simultaneous SIERRA invocations sharing allocated nodes
       if multiple jobs are started from the same directory).

The following additional environmental variables must be defined appropriately
when using the SLURM HPC environment; if they are not defined SIERRA will throw
an error.

- :envvar:`SIERRA_ARCH`

- :envvar:`PARALLEL`

.. _ln-sierra-hpc-plugins-adhoc:

Adhoc HPC Plugin
================

This HPC environment can be selected via ``--exec-env=hpc.adhoc``.

In this HPC environment, SIERRA will run experiments spread across an ad-hoc
network of compute nodes. SIERRA makes the following assumptions about the
compute nodes it is allocated each invocation:

- All nodes have a shared filesystem.

The following environmental variables must be defined appropriately when using
the Adhoc HPC environment; if they are not defined SIERRA will throw an error.

- :envvar:`SIERRA_NODEFILE`
