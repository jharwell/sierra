.. _plugins/execenv/prefectserver:

===========================================
Prefect-based Execution Environment Plugins
===========================================

SIERRA is capable of adapting its runtime infrastructure to use :term:`Prefect`
flows so that experiments can be submitted to configured prefect servers, or run
locally.

.. NOTE:: The names of prefect plugins begin with ``prefectserver`` instead of
          ``prefect`` to avoid ``sys.path`` conflicts with the ``prefect``
          package which will otherwise arise.

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


.. _plugins/execenv/prefectserver/dockerremote:

Remote+Docker Prefect Plugin
============================

.. versionadded:: 1.4.16

   Beta version. Works, but some minor rough edges/bugs may be encountered.

This prefect environment can be selected via
``--execenv=prefectserver.dockerremote``.

This plugin relies heavily on the server configuration: default queue, work
pool, etc. Currently this is not configurable (i.e., you can't specify a
specific work queue to use), but that may change in the future. In total it
assumes:

- The specified ``--docker-image`` is accessible. It doesn't have to be local;
  if will be fetched IFF it isn't found locally.

- The specified ``--docker-image`` contains the ``prefect`` executable (this is
  checked). The version of the prefect executable installed should match the
  version which SIERRA uses; if this isn't the case, you may get weird API-based
  failures.

- The prefect server+docker is setup on the machine targeted by
  :envvar:`PREFECT_API_URL` with groups/rootless docker, etc.

- There is at least one docker worker running on the prefect server in the
  default pool/pulling from the default work queue.

.. IMPORTANT:: If not using rootless docker, files within the container for all
               mounted volumes will come out owned as root unless
               ``--docker-is-host-user`` is passed.

.. list-table:: Prefect-SIERRA interface
   :widths: 25 25 50
   :header-rows: 1

   * - Prefect environment variable

     - SIERRA context

     - Command line override

   * - :envvar:`PREFECT_API_URL`

     - The URL the server is accessible at.

     - N/A
