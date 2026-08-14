.. _plugins/execenv/hpc/pbs:

PBS HPC Plugin
==============

This HPC environment can be selected via ``--execenv=hpc.pbs``.  In this HPC
environment, SIERRA will run experiments spread across multiple nodes allocated
by a scheduler from the PBS family: OpenPBS / PBS Pro, or legacy Torque.

The following table describes the PBS-SIERRA interface. Some PBS environment
variables are used by SIERRA to configure experiments during stage {1,2}; if
the required ones are not defined SIERRA will throw an error. Because OpenPBS /
PBS Pro and Torque expose per-node resources differently, :ref:`Engine` plugins
wanting to use the # of allocated cores to set run-time parameters will need to
query the environment to see which variable is available:

- ``PBS_NUM_PPN`` (Torque),
- ``NCPUS`` (OpenPBS / PBS Pro)

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

   * - :envvar:`PBS_NODEFILE`
     - Obtaining the list of nodes allocated to a job which SIERRA can direct
       GNU parallel to use for experiments.

   * - :envvar:`PBS_JOBID`
     - Creating the UUID nodelist file passed to GNU parallel, guaranteeing
       no collisions (i.e., simultaneous SIERRA invocations sharing allocated
       nodes) if multiple jobs are started from the same directory.
