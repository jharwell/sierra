.. _plugins/execenv/hpc/pbs:

PBS HPC Plugin
==============

This HPC environment can be selected via ``--execenv=hpc.pbs``.
In this HPC environment, SIERRA will run experiments spread across multiple
allocated nodes by a PBS compatible scheduler such as Moab.

The following table describes the PBS-SIERRA interface. Some PBS environment
variables are used by SIERRA to configure experiments during stage {1,2}; if
they are not defined SIERRA will throw an error.

The following environmental variables are used in the PBS HPC environment:

.. list-table:: PBS-SIERRA interface
   :header-rows: 1

   * - Environment variable
     - SIERRA context

   * - :envvar:`PARALLEL`
     - Used to transfer environment variables into the GNU parallel
       environment.

   * - :envvar:`PARALLEL_SHELL`
     - Used to set the shell used by GNU parallel to execute all commands
       in. Overwritten by SIERRA to ``/bin/bash``.

   * - :envvar:`LD_LIBRARY_PATH`
     - Exported by SIERRA via :envvar:`PARALLEL` to child GNU parallel
       processes. Can be undefined when SIERRA starts.

   * - :envvar:`PYTHONPATH`
     - Exported by SIERRA via :envvar:`PARALLEL` to child GNU parallel
       processes. Can be undefined when SIERRA starts.

   * - :envvar:`PATH`
     - Exported by SIERRA via :envvar:`PARALLEL` to child GNU parallel
       processes. Can be undefined when SIERRA starts.

   * - :envvar:`PBS_NUM_PPN`
     - Used to calculate # threads per experimental run for each allocated
       compute node via::

         floor(PBS_NUM_PPN / --exec-jobs-per-node)

       That is, ``--exec-jobs-per-node`` is required for PBS HPC environments.

   * - :envvar:`PBS_NODEFILE`
     - Obtaining the list of nodes allocated to a job which SIERRA can direct
       GNU parallel to use for experiments.

   * - :envvar:`PBS_JOBID`
     - Creating the UUID nodelist file passed to GNU parallel, guaranteeing
       no collisions (i.e., simultaneous SIERRA invocations sharing allocated
       nodes) if multiple jobs are started from the same directory.
