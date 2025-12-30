.. _plugins/execenv/hpc/slurm:

SLURM HPC Plugin
================

`<https://slurm.schedmd.com/documentation.html>`_

This HPC environment can be selected via ``--execenv=hpc.slurm``.  In this HPC
environment, SIERRA will run experiments spread across multiple nodes allocated
by the SLURM scheduler.  The following table describes the SLURM-SIERRA
interface. Some SLURM environment variables are used by SIERRA to configure
experiments during stage 1,2; if they are not defined SIERRA will throw an
error.

.. list-table:: SLURM-SIERRA interface
   :header-rows: 1

   * - Environment variable
     - SIERRA context
     - Command line override

   * - :envvar:`PARALLEL`
     - Used to transfer environment variables into the GNU parallel
       environment.
     - N/A

   * - :envvar:`PARALLEL_SHELL`
     - Used to set the shell used by GNU parallel to execute all commands
       in. Overwritten by SIERRA to ``/bin/bash``.
     - N/A

   * - :envvar:`LD_LIBRARY_PATH`
     - Exported by SIERRA via :envvar:`PARALLEL` to child GNU parallel
       processes. Can be undefined when SIERRA starts.
     - N/A

   * - :envvar:`PYTHONPATH`
     - Exported by SIERRA via :envvar:`PARALLEL` to child GNU parallel
       processes. Can be undefined when SIERRA starts.
     - N/A

   * - :envvar:`PATH`
     - Exported by SIERRA via :envvar:`PARALLEL` to child GNU parallel
       processes. Can be undefined when SIERRA starts.
     - N/A

   * - :envvar:`SLURM_CPUS_PER_TASK`
     - Used to set # threads per experimental node for each allocated compute
       node.
     - N/A

   * - :envvar:`SLURM_TASKS_PER_NODE`
     - Used to set # parallel jobs per allocated compute node.
     - ``--exec-jobs-per-node``

   * - :envvar:`SLURM_JOB_NODELIST`
     - Obtaining the list of nodes allocated to a job which SIERRA can direct
       GNU parallel to use for experiments.
     - N/A

   * - :envvar:`SLURM_JOB_ID`
     - Creating the UUID nodelist file passed to GNU parallel, guaranteeing no
       collisions (i.e., simultaneous SIERRA invocations sharing allocated nodes
       if multiple jobs are started from the same directory).
     - N/A
