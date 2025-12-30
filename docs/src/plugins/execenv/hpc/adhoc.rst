.. _plugins/execenv/hpc/adhoc:

Adhoc HPC Plugin
================

This HPC environment can be selected via ``--execenv=hpc.adhoc``.  In this HPC
environment, SIERRA will run experiments spread across an ad-hoc network of
compute nodes.

.. WARNING:: ``--sierra-root`` *MUST* be on a shared mount point across all
               nodes, or things will not work out of the box. You will have to
               manually copy things around in between stages (which you can do,
               of course).

The following environmental variables are used in the Adhoc HPC environment:

.. list-table:: Adhoc-SIERRA interface
   :header-rows: 1

   * - Environment variable
     - SIERRA context
     - Command line override

   * - :envvar:`PARALLEL`
     - Used to transfer environment variables into the GNU parallel
       environment.
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

   * - :envvar:`SIERRA_NODEFILE`
     - Contains hostnames/IP address of all compute nodes SIERRA can use. Same
       format as GNU parallel ``--sshloginfile``.  :envvar:`SIERRA_NODEFILE`
       must be defined or ``--nodefile`` passed. If neither is true, SIERRA will
       throw an error.
     - ``--nodefile``
