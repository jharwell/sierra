.. _ln-sierra-exec-env-hpc:

=================================
HPC Execution Environment Plugins
=================================

SIERRA is capable of adapting its runtime infrastructure to a number of
different HPC environments so that experiments can be run efficiently on
whatever computational resources a researcher has access to. Supported
environments that come with SIERRA are listed on this page.

These plugins tested with the following platforms (they may work on other
platforms out of the box too):

- :ref:`ln-sierra-platform-plugins-argos`

- :ref:`ln-sierra-platform-plugins-ros1gazebo`

SIERRA makes the following assumptions about the HPC environments corresponding
to the plugins listed on this page:

.. list-table:: HPC Environment Assumptions
   :widths: 25,75
   :header-rows: 1

   * - Assumption

     - Rationale

   * - All nodes allocated to SIERRA have the same # of cores (can be less than
       the total # available on each compute node). Note that this may be `less`
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
allocated nodes by a PBS compatible scheduler such as Moab.  The following table
describes the PBS-SIERRA interface. Some PBS environment variables are used by
SIERRA to configure experiments during stage 1,2 (see TOQUE-PBS docs for
meaning); if they are not defined SIERRA will throw an error.

.. list-table:: PBS-SIERRA interface
   :widths: 25,75
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

The following environmental variables are used in the PBS HPC environment:

.. list-table::
   :widths: 25,75
   :header-rows: 1

   * - Environment variable

     - Use

   * - :envvar:`SIERRA_ARCH`

     - Used to enable architecture/OS specific builds of simulators for maximum
       speed at runtime on clusters.

   * - :envvar:`PARALLEL`

     - Used to transfer environment variables into the GNU parallel
       environment. This must be always done because PBS doesn't transfer
       variables automatically, and because GNU parallel starts another level of
       child shells.

.. _ln-sierra-hpc-plugins-slurm:

SLURM HPC Plugin
================

`<https://slurm.schedmd.com/documentation.html>`_

This HPC environment can be selected via ``--exec-env=hpc.slurm``.

In this HPC environment, SIERRA will run experiments spread across multiple
allocated nodes by the SLURM scheduler. The following table describes the
SLURM-SIERRA interface. Some SLURM environment variables are used by SIERRA to
configure experiments during stage 1,2 (see SLURM docs for meaning); if they are
not defined SIERRA will throw an error.

.. list-table:: SLURM-SIERRA interface
   :widths: 25,25,50
   :header-rows: 1

   * - SLURM environment variable

     - SIERRA context

     - Command line override

   * - SLURM_CPUS_PER_TASK

     - Used to set # threads per experimental node for each allocated compute
       node.

     - N/A

   * - SLURM_TASKS_PER_NODE

     - Used to set # parallel jobs per allocated compute node.

     - ``--exec-jobs-per-node``

   * - SLURM_JOB_NODELIST

     - Obtaining the list of nodes allocated to a job which SIERRA can direct
       GNU parallel to use for experiments.

     - N/A

   * - SLURM_JOB_ID

     - Creating the UUID nodelist file passed to GNU parallel, guaranteeing no
       collisions (i.e., simultaneous SIERRA invocations sharing allocated nodes
       if multiple jobs are started from the same directory).

     - N/A

The following environmental variables are used in the SLURM HPC environment:

.. list-table::
   :widths: 25,75
   :header-rows: 1

   * - Environment variable

     - Use

   * - :envvar:`SIERRA_ARCH`

     - Used to enable architecture/OS specific builds of simulators for maximum
       speed at runtime on clusters.

   * - :envvar:`PARALLEL`

     - Used to transfer environment variables into the GNU parallel
       environment. This must be done even though SLURM can transfer variables
       automatically, because GNU parallel starts another level of child
       shells.

.. _ln-sierra-hpc-plugins-adhoc:

Adhoc HPC Plugin
================

This HPC environment can be selected via ``--exec-env=hpc.adhoc``.

In this HPC environment, SIERRA will run experiments spread across an ad-hoc
network of compute nodes. SIERRA makes the following assumptions about the
compute nodes it is allocated each invocation:

- All nodes have a shared filesystem.

The following environmental variables are used in the Adhoc HPC environment:

.. list-table::
   :widths: 25,25,25,25
   :header-rows: 1

   * - Environment variable

     - SIERRA context

     - Command line override

     - Notes

   * - :envvar:`SIERRA_NODEFILE`

     - Contains hostnames/IP address of all compute nodes SIERRA can use. Same
       format as GNU parallel ``--sshloginfile``.

     - ``--nodefile``

     - :envvar:`SIERRA_NODEFILE` must be defined or ``--nodefile`` passed. If
       neither is true, SIERRA will throw an error.
