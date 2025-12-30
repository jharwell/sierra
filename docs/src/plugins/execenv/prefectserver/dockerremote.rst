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
