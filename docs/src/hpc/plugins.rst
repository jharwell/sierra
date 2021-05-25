.. _ln-hpc-plugins:

========================================
High Performance Computing (HPC) Plugins
========================================

SIERRA is capable of adapting its runtime infrastructure to a number of
different HPC environments so that ARGoS experiments can be run efficiently on
whatever computational resources a researcher has access to. Supported
environments that come with SIERRA are:

- :ref:`src/hpc/plugins:Local`
- :ref:`src/hpc/plugins:PBS`
- :ref:`src/hpc/plugins:SLURM`
- :ref:`src/hpc/plugins:Adhoc`

Local
=====

This HPC environment can be selected via ``--hpc-env=local``.

This is the default HPC environment in which SIERRA will all experiments on the
same computer from which it was launched using GNU parallel.  The # simultaneous
simulations will be determined by::

  # cores on machine / # selected physics engines

Consequently, the ``--physics-n-engines`` option is required for this HPC
environment during stage 1.  If more simulations are requested than can be run
in parallel, SIERRA will start additional simulations as currently running
simulations finish.

No additional configuration/environment variables are needed with this HPC
environment for use with SIERRA.

PBS
===

This HPC environment can be selected via ``--hpc-env=pbs``.

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
     - Used to calculate # physics engines per simulation for each allocated compute
       node via::

         floor(PBS_NUM_PPN / ``--exec-sims-per-node``)

       That is, ``--exec-sims-per-node`` is required for PBS HPC environments.

   * - PBS_NODEFILE

     - Obtaining the list of nodes allocated to a job which SIERRA can direct GNU
       parallel to use for experiments.

   * - PBS_JOBID

     - Creating the UUID nodelist file passed to GNU parallel, guaranteeing
       no collisions (i.e., simultaneous SIERRA invocations sharing allocated
       nodes) if multiple jobs are started from the same directory.

The following environmental variables must be defined appropriately when using
the PBS HPC environment:

- :envvar:`SIERRA_ARCH`
- :envvar:`PARALLEL`

SLURM
=====

`<https://slurm.schedmd.com/documentation.html>`_

This HPC environment can be selected via ``--hpc-env=slurm``.

In this HPC environment, SIERRA will run experiments spread across multiple
allocated nodes by the SLURM scheduler Moab. SIERRA makes the following
assumptions about the compute nodes it is allocated each invocation:

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
     - Used to set # physics engines per simulation for each allocated compute
       node.

   * - SLURM_TASKS_PER_NODE
     - Used to set # parallel jobs per allocated compute node. Overriden by
       ``--exec-sims-per-node`` if passed.

   * - SLURM_JOB_NODELIST

     - Obtaining the list of nodes allocated to a job which SIERRA can direct GNU
       parallel to use for experiments.

   * - SLURM_JOB_ID

     - Creating the UUID nodelist file passed to GNU parallel, guaranteeing
       no collisions (i.e., simultaneous SIERRA invocations sharing allocated
       nodes`` if multiple jobs are started from the same directory.

The following environmental variables must be defined appropriately when using
the SLURM HPC environment:

- :envvar:`SIERRA_ARCH`
- :envvar:`PARALLEL`

Adhoc
=====

This HPC environment can be selected via ``--hpc-env=adhoc``.

In this HPC environment, SIERRA will run experiments spread across an ad-hoc
network of compute nodes. SIERRA makes the following assumptions about the
compute nodes it is allocated each invocation:

- All nodes have a shared filesystem.

The following environmental variables must be defined appropriately when using
the Adhoc HPC environment:

- :envvar:`SIERRA_ADHOC_NODEFILE`
