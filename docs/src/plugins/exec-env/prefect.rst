.. _plugins/exec-env/prefect:

===========================================
Prefect-based Execution Environment Plugins
===========================================

SIERRA is capable of adapting its runtime infrastructure to use :term:`Prefect`
flows so that experiments can be submitted to configured prefect servers, or run
locally. SIERRA makes the following assumptions about the prefect environments
corresponding to the plugins listed on this page:

.. list-table:: HPC Environment Assumptions
   :widths: 25 75
   :header-rows: 1

   * - Assumption

     - Rationale

   * - All nodes on which jobs are run have a shared filesystem which contains
       ``--sierra-root``.

     - Standard feature on cluster/HPC environments. If for some reason this is
       not true, stage 2 outputs will have to be manually placed such that it is
       as if everything ran on a common filesystem prior to running any later
       stages.

.. _plugins/exec-env/prefect/local:

Local Prefect Plugin
====================

.. versionadded:: 1.4.15

   Beta version. Works, but some minor rough edges bugs may be encountered.

This prefect environment can be selected via ``--exec-env=prefect.local``.  This
plugin defines the following prefect artifacts:

- ``sierra/local`` flow to execute all :term:`Experimental Runs <Experimental
  Run>` in each :term:`Experiment` in parallel.

- ``sierra-pool`` work pool which the prefect workers live in. The # workers is
  determined by the selected :term:`Engine` and/or ``--exec-jobs-per-node``.

- ``sierra-queue`` work queue which the SIERRA prefect workers pull tasks from.

Obviously, if you use this execution environment, don't define artifacts with
the same name in prefect or things will (probably) not work.

A local prefect server is spun up for the :term:`Batch Experiment`. Currently,
multiple SIERRA users using this plugin on the same server is not supported,
though it could be easily if randomized ports are used.

.. list-table:: Prefect-SIERRA interface
   :widths: 25 25 50
   :header-rows: 1

   * - Prefect environment variable

     - SIERRA context

     - Command line override

   * - :envvar:`PREFECT_API_URL`

     - The URL the server is accessible at. Not currently configurable.

     - N/A


.. _plugins/exec-env/prefect/dockerremote:

Remote+Docker Prefect Plugin
============================

This prefect environment can be selected via
``--exec-env=prefect.dockerremote``.

In this environment, SIERRA will:

- Run a flow to build a docker image, as specified on the cmdline, before
  running any experiments.

- Submit all jobs in each :term:`Experiment` within a :term:`Batch Experiment`
  serially to the server, and wait for their completion before moving to the
  next experiment. The following table describes the Prefect-SIERRA
  interface. Some environment variables are used by SIERRA to configure
  experiments during stage 1,2 (see prefect docs for meaning); if they are not
  defined SIERRA will throw an error.

.. list-table:: Prefect-SIERRA interface
   :widths: 25 25 50
   :header-rows: 1

   * - Prefect environment variable

     - SIERRA context

     - Command line override

   * - :envvar:`PREFECT_API_URL`

     - The URL the server is accessible at.

     - N/A
