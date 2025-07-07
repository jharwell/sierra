.. _plugins/exec-env/prefect:

==========================================
Prefect-base Execution Environment Plugins
==========================================

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

This prefect environment can be selected via ``--exec-env=prefect.local``.

The # simultaneous simulations will be whatever the default for prefect is
(usually the # of cores on the local machine). A local server will be spun up
per-:term:`Experiment`. This introduces some unavoidable overhead when running
Prefect locally; this execution environment is meant as a stepping
stone to a remote Prefect-based execution environment, or as a debugging option.

No additional configuration/environment variables are needed with this
environment for use with SIERRA.

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
