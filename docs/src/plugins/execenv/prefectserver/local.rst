.. _plugins/execenv/prefectserver/local:

Local Prefect Server Plugin
===========================

.. versionadded:: 1.4.15

   Beta version. Works, but some minor rough edges/bugs may be encountered.

This prefect environment can be selected via ``--execenv=prefect.localserver``.
This plugin defines the following prefect artifacts:

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

.. WARNING::

   As of 2025/7/29 prefect=3.4.3, there does not appear to be any way to
   limit the concurrency at the task-level (which is what SIERRA uses), so it is
   not currently possible to limit # simultaneously active
   runs/simulations. This means that (a) multiple users using the execution
   environment on the same server will not work well, and (b) simulation engines
   which use multiple threads for a single experimental run can easily overload
   the local machine if ``--n-runs >= # cores on machine / # threads per run``.

.. list-table:: Prefect-SIERRA interface
   :widths: 25 25 50
   :header-rows: 1

   * - Prefect environment variable

     - SIERRA context

     - Command line override

   * - :envvar:`PREFECT_API_URL`

     - The URL the server is accessible at. Not currently configurable. The docs
       *say* it's configurable, but it doesn't work afaict. This means that
       multiple concurrent users of SIERRA using this plugin will probably not
       work.

     - N/A
