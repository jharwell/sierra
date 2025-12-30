.. _plugins/execenv/hpc/awsbatch:

AWS Batch HPC Plugin
====================

.. versionadded:: 1.5.7

`<https://aws.amazon.com/batch/>`_

This HPC environment can be selected via ``--execenv=hpc.awsbatch``.  SIERRA
will run experiments spread across multiple nodes, as defined by the job
definition in used to submit the job SIERRA runs in. All jobs run in docker
containers, so the container must be specified as part of the job definition. In
this plugin, SIERRA expects:

- To be run as node 0 in a *multi-node array job*.

- Nodes > 0 will wait/not exit until SIERRA finishes/exits on node 0. A common
  bash script with a variable being set/unset by the node 0 job is a simple way
  to accomplish this.

- All nodes in ``--nodefile`` or :envvar:`SIERRA_NODEFILE` are available when
  SIERRA starts. This generally means node 0 needs to wait/poll worker nodes
  until they are all available, and *then* launching SIERRA.

- All nodes have the same # CPUs allocated to them.

- Nodes can communicate with each other via ssh on port 22.

.. WARNING:: ``--sierra-root`` *MUST* be on a shared EFS mount/something
             similar in the docker image, or things will not work.

Basically, you have something like this::

  ┌────────────────────────────────────────────────────────────────────┐
  │                         Shared Storage (EFS,...)                   │
  │                       fs-12345678 mounted at /mnt/efs              │
  └────────────────────────────────────────────────────────────────────┘
           ▲              ▲              ▲              ▲
           │              │              │              │
      Mount /mnt/efs on all nodes (read/write shared)   │
           │              │              │              │
  ┌────────┴───────┐ ┌────┴───────┐ ┌────┴───────┐ ┌────┴───────┐
  │   Node 0       │ │  Node 1    │ │  Node 2    │ │  Node 3    │
  │   (MAIN)       │ │ (Worker)   │ │ (Worker)   │ │ (Worker)   │
  │ 10.0.1.10      │ │ 10.0.1.11  │ │ 10.0.1.12  │ │ 10.0.1.13  │
  │                │ │            │ │            │ │            │
  │ 10 vCPUs       │ │ 10 vCPUs   │ │ 10 vCPUs   │ │ 10 vCPUs   │
  │ 8GB RAM        │ │ 8GB RAM    │ │ 8GB RAM    │ │ 8GB RAM    │
  │                │ │            │ │            │ │            │
  │ SSH daemon ✓   │ │ SSH daemon │ │ SSH daemon │ │ SSH daemon │
  └────────────────┘ └────────────┘ └────────────┘ └────────────┘
           │              ▲              ▲              ▲
           │              │              │              │
           │         SSH connections to execute tasks   │
           │              │              │              │
           └──────────────┴──────────────┴──────────────┘
                          │
                ┌─────────┴─────────┐
                │  SIERRA           │
                │  (runs on Node 0) │
                └───────────────────┘


The following table describes the AWS Batch-SIERRA interface. Some environment
variables are used by SIERRA to configure experiments during stage 1,2; if they
are not defined SIERRA will throw an error.

.. list-table:: AWS Batch-SIERRA interface
   :header-rows: 1

   * - Environment variable
     - SIERRA context
     - Command line override

   * - :envvar:`PARALLEL`
     - Used to transfer environment variables into the GNU parallel
       environment. SIERRA appends to this variable. Can be undefined when
       SIERRA starts.
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

   * - :envvar:`AWS_BATCH_JOB_NUM_NODES`
     - Obtaining the list of nodes allocated to a job which SIERRA can direct
       GNU parallel to use for experiments.
     - N/A

   * - :envvar:`AWS_BATCH_JOB_ID`
     - Creating the UUID nodelist file passed to GNU parallel, guaranteeing no
       collisions (i.e., simultaneous SIERRA invocations sharing allocated nodes
       if multiple jobs are started from the same directory).
     - N/A

   * - :envvar:`SIERRA_NODEFILE`
     - Contains hostnames/IP address of all compute nodes SIERRA can use. Same
       format as GNU parallel ``--sshloginfile``.  :envvar:`SIERRA_NODEFILE`
       must be defined or ``--nodefile`` passed. If neither is true, SIERRA will
       throw an error.
     - ``--nodefile``
