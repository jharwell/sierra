.. _plugins/execenv/hpc:

=================================
HPC Execution Environment Plugins
=================================

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


You may want to built e.g., GoS natively for your HPC cluster for maximum
efficiency; if your HPC cluster is 1/2 Intel chips and 1/2 AMD chips, you may
want to compile your :term:`Engine` twice, natively on each chipset. If you do
this, you can set :envvar:`SIERRA_ARCH` prior to invoking SIERRA so that the
correct invocation commands can be generated, depending on what the chipset is
for the nodes you request for your HPC job.

Similarly, you may want to build your :term:`Project` ``.so`` (if your project
is C/C++) natively on each different type of compute node SIERRA might be run
on, just like ARGOS, for maximum efficiency with systems.

.. _plugins/execenv/hpc/local:

Local HPC Plugin
================

This HPC environment can be selected via ``--execenv=hpc.local``.

This is the default HPC environment in which SIERRA will run all
:term:`Experimental Runs <Experimental Run>` on the same computer from which it
was launched using GNU parallel.  The # simultaneous simulations will be
determined by a number of factors, including:

- ``--exec-jobs-per-node``

- The selected :term:`Engine`'s parallelism paradigm and its specific
  configuration.

- The # of cores on the machine.

This HPC environment supports both ``per-batch`` and ``per-exp`` parallelism
paradigms. If more simulations are requested than can be run in parallel, SIERRA
will start additional simulations as currently running simulations finish. No
additional configuration/environment variables are needed with this HPC
environment for use with SIERRA.

The following environmental variables are automatically exported to child GNU
parallel processes in the local HPC environment:

The following environmental variables are used in the local HPC environment:

.. list-table::
   :header-rows: 1

   * - Environment variable

     - SIERRA context


   * - :envvar:`PARALLEL`

     - Used to transfer environment variables into the GNU parallel
       environment. SIERRA appends to this variable.

   * - :envvar:`LD_LIBRARY_PATH`

     - Exported by SIERRA via :envvar:`PARALLEL` to child GNU parallel
       processes.


.. _plugins/execenv/hpc/pbs:

PBS HPC Plugin
==============

This HPC environment can be selected via ``--execenv=hpc.pbs``.

In this HPC environment, SIERRA will run experiments spread across multiple
allocated nodes by a PBS compatible scheduler such as Moab.  The following table
describes the PBS-SIERRA interface. Some PBS environment variables are used by
SIERRA to configure experiments during stage 1,2 (see TOQUE-PBS docs for
meaning); if they are not defined SIERRA will throw an error.

The following environmental variables are used in the PBS HPC environment:

.. list-table:: PBS-SIERRA interface
   :header-rows: 1

   * - Environment variable

     - SIERRA context

   * - :envvar:`PARALLEL`

     - Used to transfer environment variables into the GNU parallel
       environment. SIERRA appends to this variable.

   * - :envvar:`LD_LIBRARY_PATH`

     - Exported by SIERRA via :envvar:`PARALLEL` to child GNU parallel
       processes.

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


.. _plugins/execenv/hpc/slurm:

SLURM HPC Plugin
================

`<https://slurm.schedmd.com/documentation.html>`_

This HPC environment can be selected via ``--execenv=hpc.slurm``.

In this HPC environment, SIERRA will run experiments spread across multiple
allocated nodes by the SLURM scheduler. The following table describes the
SLURM-SIERRA interface. Some SLURM environment variables are used by SIERRA to
configure experiments during stage 1,2 (see SLURM docs for meaning); if they are
not defined SIERRA will throw an error.

.. list-table:: SLURM-SIERRA interface
   :header-rows: 1

   * - Environment variable

     - SIERRA context

     - Command line override

   * - :envvar:`PARALLEL`

     - Used to transfer environment variables into the GNU parallel
       environment. SIERRA appends to this variable.

     - N/A

   * - :envvar:`LD_LIBRARY_PATH`

     - Exported by SIERRA via :envvar:`PARALLEL` to child GNU parallel
       processes.

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

.. _plugins/execenv/hpc/adhoc:

Adhoc HPC Plugin
================

This HPC environment can be selected via ``--execenv=hpc.adhoc``.

In this HPC environment, SIERRA will run experiments spread across an ad-hoc
network of compute nodes. SIERRA makes the following assumptions about the
compute nodes it is allocated each invocation:

- All nodes have a shared filesystem.

The following environmental variables are used in the Adhoc HPC environment:

.. list-table:: Adhoc-SIERRA interface
   :header-rows: 1

   * - Environment variable

     - SIERRA context

     - Command line override

   * - :envvar:`PARALLEL`

     - Used to transfer environment variables into the GNU parallel
       environment. SIERRA appends to this variable.

     - N/A

   * - :envvar:`LD_LIBRARY_PATH`

     - Exported by SIERRA via :envvar:`PARALLEL` to child GNU parallel
       processes.

     - N/A

   * - :envvar:`SIERRA_NODEFILE`

     - Contains hostnames/IP address of all compute nodes SIERRA can use. Same
       format as GNU parallel ``--sshloginfile``.  :envvar:`SIERRA_NODEFILE`
       must be defined or ``--nodefile`` passed. If neither is true, SIERRA will
       throw an error.

     - ``--nodefile``
